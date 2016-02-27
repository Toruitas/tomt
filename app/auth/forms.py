__author__ = 'Stuart'
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo
from flask.ext.pagedown.fields import PageDownField
from ..models import User

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(message="Please enter an email address."),
                                             Length(1,64, message="Between 1 and 64 characters long please."),
                                             Email(message="Please enter a valid email address")],
                        )
    password = PasswordField('Password', validators=[DataRequired("Please enter a password.")])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField("Log In")


class RegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              message='Username must have only letters, numbers, dots, or underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message="Passwords must match.")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Register')

    def validate_email(self, field):
        """
        When a form defines a method with prefix validate_ followed by name of a field,
        the method is invoked in addition to any regularly defined validators. In this case,
        custom validators for email and username ensure values aren't duplicates.
        :param field:
        :return:
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered")

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')