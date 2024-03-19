import re
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo


def character_check(form, field):
    excluded_chars = set("* ? ! ' ^ + % & / ( ) = } ] [ { $ # @ < >")

    for char in field.data:
        if char in excluded_chars:
            raise ValidationError(f"Character {char} is not allowed.")


def valid_phone(form, phone):
    phone_regex = r'^\d{4}-\d{3}-\d{4}$'
    if not re.match(phone_regex, phone.data):
        raise ValidationError("Invalid phone number format. Please use XXXX-XXX-XXXX.")


def valid_dob(form, field):
    dob_regex = r'^(0[1-9]|[1-2]\d|3[0-1])/(0[1-9]|1[0-2])/(19|20)\d{2}$'
    if not re.match(dob_regex, field.data):
        raise ValidationError("Invalid date of birth format, Please use DD/MM/YYYY. ")


def valid_postcode(form, field):
    postcode_regex = r'^[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][ABD-HJLNP-UW-Z]{2}$'
    if not re.match(postcode_regex, field.data):
        raise ValidationError("Invalid postcode format, Please use appropriate format: XY YXX, XYY YXX, or XXY YXX. ")


def valid_password(form, password):
    p = re.compile(r'(?=.*\d)(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>])')
    if not p.match(password.data):
        raise ValidationError("Password must contain at least 1 digit, at least 1 lowercase and at least 1 uppercase "
                              "word character")


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    date_of_birth = StringField('Date of Birth', validators=[DataRequired(), Length(min=10, max=10)])
    postcode = StringField('Postcode', validators=[DataRequired(), Length(min=5, max=8)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = EmailField(validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    pin_key = StringField(validators=[DataRequired()])
    postcode = StringField(validators=[DataRequired()])
    reCaptcha = RecaptchaField()
    submit = SubmitField('Login')


class PasswordForm(FlaskForm):
    current_password = PasswordField(id='Password', validators=[DataRequired()])
    show_password = BooleanField('Show Password', id='check')
    new_password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=12,
                                                                                message='Must be between 6-12 characters'),
                                                         valid_password])
    confirm_new_password = PasswordField('Password', validators=[DataRequired(), EqualTo('new_password',
                                                                                         message='Both password must be equal')])
    submit = SubmitField('Change Password')
