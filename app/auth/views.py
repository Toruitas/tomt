__author__ = 'Stuart'

"""
Authentication stuff.
Registration.
Log in.
Log out.
Make sure to add Oauthlib stuff after email included.
"""

from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_grid_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm,\
    ChangeEmailForm

# @auth.before_app_request  # intercepts request under these conditions
# def before_request():
#     """
#     When a before_request or before_app_request callback returns a
#     response or a redirect, Flask sends that to the client without invoking
#     the view function associated with the request. This effectively
#     allows these callbacks to intercept a request when necessary.
#
#     From a blueprint, the before_request hook applies only to requests that
#     belong to the blueprint. To install a hook for all application requests from a blueprint,
#     the before_app_request decorator must be used instead.
#
#     The requested endpoint (accessible as request.endpoint) is outside of the authentication
#     blueprint. Access to the authentication routes needs to be granted, as
#     those are the routes that will enable the user to confirm the account or perform
#     other account management functions.
#
#     This is really annoying. Change it so that it is only a flash.
#     :return:
#     """
#     if current_user.is_authenticated():
#         current_user.ping()
#         if not current_user.confirmed:
#             flash("Remember to authenticate.")
        # if not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
        #     return redirect(url_for('auth.unconfirmed'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Make sure to do this with HTTPS in production
    :return:
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET','POST'])
def register():
    """
    Add captcha
    :return:
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username = form.username.data,
                    password = form.password.data,
                    )
        db.session.add(user)
        db.session.commit()  # even though app autocommits at end of request, we need to do it explicit now since need
                                # id for token creation
        token = user.generate_confirmation_token()
        send_grid_email(user.email, 'Confirm Your Account','auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:  # if user already confirmed, just goes to index
        return redirect(url_for('main.index'))
    if current_user.confirm(token):  # confirmation done in the User class, changes .confirmed attribute
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    """
    Need Captcha
    :return:
    """
    token = current_user.generate_confirmation_token()
    send_grid_email(current_user.email,
               'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

@auth.route('/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()

            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)

@auth.route('/reset/', methods=['GET', 'POST'])
def password_reset_request():
    # if current_user.is_anonymous:
    #     return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_grid_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    """
    Change this so that emails aren't changed until confirmation is done.
    :return:
    """
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_grid_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))