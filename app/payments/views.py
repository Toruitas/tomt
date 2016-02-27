__author__ = 'Stuart'
import stripe
from . import payments
from flask import current_app, render_template, request, flash
from flask.ext.login import current_user, login_required, redirect, url_for, session
from .. import db
from ..email import send_grid_email


@payments.route('/confirm')
@login_required
def confirm():
    # https://dashboard.stripe.com/test/dashboard
    key = current_app.config['STRIPE_KEYS']['publishable_key']
    return render_template('payments/confirm.html', key=key, amount = session['amount'])

@payments.route('/thanks/<int:id>')
def thanks(id):
    # how do we do a countdown to redirect? Javascript I guess.
    #     flash('Woo! Your pot has been created - but we still need to check it out before we let it into the wild.')
    #     sleep(5)
    #     return redirect('main.index')
    return render_template("payments/thanks.html", id=id)