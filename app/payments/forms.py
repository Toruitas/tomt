from flask.ext.wtf import Form
from wtforms import SubmitField

class ConfirmForm(Form):
    submit=SubmitField("Confirm")