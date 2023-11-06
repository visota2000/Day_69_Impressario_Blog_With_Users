from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditor, CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("ブログ記事タイトル", validators=[DataRequired()])
    subtitle = StringField("サブタイトル", validators=[DataRequired()])
    img_url = StringField("記事画像のURL", validators=[DataRequired(), URL()])
    body = CKEditorField("記事の内容", validators=[DataRequired()])
    submit = SubmitField("ブログ記事を投稿する")

class RegisterForm(FlaskForm):
    email = EmailField('メールアドレスをご入力ください', validators=[DataRequired()])
    name = StringField('氏名をご入力ください', validators=[DataRequired(), Length(6, 100)])
    password =  PasswordField('パスワードをご入力ください', validators=[DataRequired(), Length(6, 100)])
    submit = SubmitField('送信する')

class LoginForm(FlaskForm):
    email=EmailField('メールアドレスをご入力ください', validators=[DataRequired()])
    password=PasswordField('パスワードをご入力ください', validators=[DataRequired(), Length(6, 100)])
    submit = SubmitField('送信する')

class CommentForm(FlaskForm):
    comment_text = CKEditorField("コメントをご入力ください.【ご注意】コメントを投稿するにはログインしてください。", validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField("コメントを投稿する")

class ContactForm(FlaskForm):
    email=EmailField('メールアドレスをご入力ください', validators=[DataRequired()])
    name = StringField('氏名をご入力ください', validators=[DataRequired()])
    message_subject=StringField('メールのテーマをご入力ください', validators=[DataRequired()])
    message = StringField('メッセージをご入力ください', validators=[DataRequired()])
    submit = SubmitField("送信する")
