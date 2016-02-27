from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, RadioField, SelectField, ValidationError, IntegerField
from wtforms.validators import DataRequired, Length, Email, Regexp
from flask.ext.pagedown.fields import PageDownField
from ..models import User, Role, Question, Answer

class CreateQuestionForm(Form):
    title = StringField("What's your burning question?", validators=[DataRequired()])
    description = PageDownField('Give as many helpful details as you can think of', validators=[DataRequired()])
    category = RadioField("Pick a category", validators=[DataRequired()],
                          choices= [("music","Music"),("people","People"),("movies","Movies"),("tv","TV"),
                                    ("things","Things"),("things","Language"),("nsfw","NSFW"),("art","Art")]) #  ('value','description')
    submit = SubmitField('Submit')

class ReportForm(Form):
    title = StringField("What is the nature of your medical emergency?", validators=[Length(1,128),DataRequired()])
    complaint = StringField("Please, elaborate...", validators=[DataRequired()])
    submit = SubmitField('Send Report')

class EditQuestionForm(Form):
    description = PageDownField('Give as many helpful details as you can think of', validators=[DataRequired()])
    category = RadioField("Pick a category", validators=[DataRequired()],
                          choices= [("music","Music"),("people","People"),("movies","Movies"),("tv","TV"),
                                    ("things","Things"),("things","Language"),("nsfw","NSFW"),("art","Art")])
    submit = SubmitField('Submit')

class CreateAnswerForm(Form):
    answer = PageDownField('Answer the question as best you can', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditAnswerForm(Form):
    answer = PageDownField('Edit your answer to the above question.', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AcceptAnswerForm(Form):
    submit = SubmitField('Accept this answer')

