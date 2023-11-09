import smtplib
import os
from dotenv import load_dotenv

import lxml as lxml
import lxml.html
from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory,session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column, Integer, ForeignKey
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
from flask_gravatar import Gravatar
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, EmailField,  PasswordField
from wtforms.validators import DataRequired, Length
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm
from functools import wraps
from flask import abort
import bleach
from dotenv import load_dotenv


load_dotenv('.env')
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD") ##Using App Password instead of common Gggole email password
##For details of Google App Password see https://towardsdatascience.com/automate-sending-emails-with-gmail-in-python-449cc0c3c317


app = Flask(__name__) #creating a Flask type object
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# ##CONNECT TO DB
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DAY_69_70_DB_URL")
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# CONNECT TO DB
if os.environ.get("LOCAL") == "True":
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DAY_69_70_DB_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")

app.app_context().push()
db = SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


## strips invalid tags/attributes
def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                    'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul']

    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }

    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)

    return cleaned

##CREATE TABLE of registered users IN DB
class User(UserMixin, db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts=relationship("BlogPost", back_populates="author")#Create reference to the BlogPost object, back_populates="author" refers to the protperty in the BlogPosts class. For details see Day_69_One_to_Many_backpopulate.png
    comments=relationship("Comment", back_populates="comment_author")
    def set_password(self, entered_password):
        self.password=generate_password_hash(entered_password, method="pbkdf2:sha256", salt_length=8)

    def check_password(self, entered_password):
        return check_password_hash(self.password,entered_password)


##CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id")) #Create Foreign Key, "users.id" the users refers to the tablename of User. For details see Day_69_One_to_Many_backpopulate.png
    author = relationship("User", back_populates="posts") #Create reference to the User object, back_populates="posts" refers to the posts protperty in the User class. For details see "E:\PycharmProjects\Day_69_One_to_Many_backpopulate.png"
    comments= relationship("Comment", back_populates="parent_post")


#Line below only required once, when creating DB.
class Comment(db.Model):
    __tablename__="comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id=db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author=relationship("User", back_populates="comments")
    comment_text = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()



#Create admin-only decorator
def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # only the user with id=1 can access this func
        # to catch the unauthenticated we use (not current_user.is_authenticated) or (current_user.is_anonymous)
        if current_user.is_anonymous or current_user.id!=1:
            return "<h1>アクセスが拒否されました (Forbidden)</h1><p>このアクションを実行するためのアクセス権が不足しています。(Insufficient access privileges to perform this action.)</p>",403
        elif current_user.id ==1:
        # Otherwise continue with the route function
            return function(*args, **kwargs)
    return decorated_function

@app.route('/', methods=["GET","POST"])
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        email=form.email.data
        # If user's email already exists
        if User.query.filter_by(email=email).first():
            ##Send flash messsage
            flash("すでにメールでサインアップ済みですので、代わりにログインをお試しください。")
            # Redirect to /login route.
            return redirect(url_for('login'))
        else:
            new_user=User(name=form.name.data,
                          email=form.email.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            # Log in and authenticate user after adding details to database.
            login_user(new_user)
            return redirect (url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    login_form=LoginForm()
    if login_form.validate_on_submit():
        email=login_form.email.data
        password=login_form.password.data

        user=db.session.query(User).filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("申し訳ございませんが、ご利用のメールアドレスに関連するアカウントが見つかりませんでした。再度ログインをお試しいただくか、新しいアカウントを作成していただけますと幸いです。")
            return redirect(url_for("login"))
        # Password incorrect
        elif not user.check_password(password):
            flash('ご入力いただいたユーザー名またはパスワードが正しくありません。再度ご確認いただき、お試しいただけますと幸いです。')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template('login.html', form=login_form, current_user=current_user)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET","POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form=CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please login or register to make a comment")
            return redirect(url_for('login'))
        else:
            new_comment=Comment(
                comment_text=strip_invalid_html(comment_form.comment_text.data),
                parent_post=requested_post,
                comment_author=current_user,
                )
            db.session.add(new_comment)
            db.session.commit()
            comment_form.comment_text.data = "" #The comment text persists in the box after submission because the browser restores the form state after page reload, including the text entered in the CKEditor text box. This behavior is called form autofill. Clearing it with the addition of:  form.comment_text.data = ""   is a fine solution to this problem

    return render_template("post.html", post=requested_post, form=comment_form, current_user=current_user)


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/new-post", methods=["GET","POST"])
@login_required
@admin_only ##Mark with decorator
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        year = date.today().strftime("%Y")
        month = date.today().strftime("%m")
        day = date.today().strftime("%d")
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user, #Чтобы сработал One to Many relashionship, здесь надо передавать не current_user.name (это "str"), а curent_user (object)
            date=f"{year}年{month}月{day}日"
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>", methods=["GET","POST"])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():

        send_mail(fromaddr=MY_EMAIL,
                  toaddr=MY_EMAIL,
                  user_email=strip_invalid_html(contact_form.email.data),
                  name=strip_invalid_html(contact_form.name.data),
                  subject=f'Email from my Blog Capstone Project: {strip_invalid_html(contact_form.message_subject.data)}',
                  message=strip_invalid_html(contact_form.message.data))
        contact_form = ContactForm(formdata=None)
        return render_template("contact.html", msg_sent=True, form=contact_form)
    return render_template("contact.html", msg_sent=False, form=contact_form)

def send_mail(fromaddr, toaddr,name, user_email,  subject, message):
    msg = MIMEMultipart('related')
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    body = f"From: {user_email} <br> Sender's name: {name} <br> Message: {message}"
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    part_text = MIMEText(lxml.html.fromstring(body).text_content().encode('utf-8'), 'plain', _charset='utf-8')
    part_html = MIMEText(body.encode('utf-8'), 'html', _charset='utf-8')
    msg_alternative.attach(part_text)
    msg_alternative.attach(part_html)
    server = smtplib.SMTP("smtp.gmail.com",port= 587, timeout=120)
    server.starttls()
    server.login(user=MY_EMAIL, password=APP_PASSWORD)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()


if __name__ == "__main__":
    app.run(debug=True) #changet from False to True

