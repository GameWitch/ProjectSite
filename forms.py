from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, MultipleFileField, SelectField, FileField
from wtforms.validators import DataRequired, URL, Length, Regexp
from flask_ckeditor import CKEditorField


# #WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    project_type = SelectField('Project Type', choices=['Python', 'Game'])
    play_game_page = StringField("Name of Play Page")
    images = MultipleFileField("Image Files")
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("E-mail Address", validators=[DataRequired()])
    body = CKEditorField("Message", validators=[DataRequired()])
    submit = SubmitField("Send Message")


class RegisterForm(FlaskForm):
    email = StringField("email", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired(),
                                                     Length(min=8, message="Password must be at least 8 characters long"),
                                                     Regexp("(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)",
                                                            message="Must include at least 1 capital letter at least 1 lower case number, and at least 1 number and 1 special character ")])
    passwordtwo = PasswordField("password", validators=[DataRequired(),
                                                        Length(min=8, message="Password must be at least 8 characters long"),
                                                        Regexp("(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)",
                                                            message="Must include at least 1 capital letter at least 1 lower case number, and at least 1 number and 1 special character ")])
    name = StringField('name', validators=[DataRequired()])
    submit = SubmitField("Sign up!")


class LoginForm(FlaskForm):
    email = StringField("email", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("Log in.")


class CommentForm(FlaskForm):
    body = CKEditorField("Comment On Post", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LandlordForm(FlaskForm):
    number = StringField("Number", validators=[DataRequired()])
    direction = SelectField("Direction", validators=[DataRequired()], choices=["N", "S", "E", "W"])
    street = StringField("Street Name", validators=[DataRequired()])
    st_type = SelectField("Type of Road", validators=[DataRequired()], choices=["ST", "AVE", "PKWY", "BLVD", "CT", "PL", "RD", "CIR", "DR", "WAY", "LN", "HWY"])
    submit = SubmitField("Submit")


class UpdateLandlordForm(FlaskForm):
    excel = FileField("File")
    submit = SubmitField("Submit")