from threading import Thread
from flask import current_app, render_template
from flask.ext.mail import Message
import sendgrid
from . import mail

def send_async_grid_email(app, msg, sg):
    with app.app_context():
        status, msg = sg.send(msg)

def send_grid_email(to, subject, template, **kwargs):
    """
    https://github.com/sendgrid/sendgrid-python

    API keys upgrade when SendGridClient upgraded to 2.0.
    :param to:
    :param subject:
    :param template:
    :param kwargs:
    :return:
    """

    app = current_app._get_current_object()
    sg = sendgrid.SendGridClient(app.config['SENDGRID_USERNAME'], app.config['SENDGRID_PASSWORD'], raise_errors=True)

    message = sendgrid.Mail(
        to=[to],
        subject=app.config['TIP_MAIL_SUBJECT_PREFIX'] +' '+ subject,
        html=render_template(template + '.html', **kwargs),
        text=render_template(template + '.txt', **kwargs),
        from_email=app.config['TIP_MAIL_ADDRESS'],
        from_name=app.config['TIP_MAIL_SENDER']
    )
    thr = Thread(target=send_async_grid_email, args=[app, message, sg])
    thr.start()
    return thr