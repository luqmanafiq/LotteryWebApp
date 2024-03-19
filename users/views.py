# IMPORTS
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from flask_login import login_user, logout_user, login_required, current_user
from markupsafe import Markup

from app import db, logger
from models import User
from users.forms import RegisterForm, LoginForm, PasswordForm

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        postcode=form.postcode.data,
                        password=form.password.data,
                        role='user')

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        session['email'] = new_user.email

        if 'email' not in session:
            return redirect(url_for('index'))
        # sends user to 2fa page
        return redirect(url_for('users.setup_2fa'))

    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


@users_blueprint.route('/setup-2fa')
def setup_2fa():
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('index'))

    del session['email']

    return render_template('users/setup-2fa.html', email=user.email, uri=user.get_2fa_uri()), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


# view user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if not session.get('authentication_attempts'):
        session['authentication_attempts'] = 0

    if form.validate_on_submit():
        # Submitted Username, Password and Time-based PIN + Postcode must be compared/validated against existing data
        # in database
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not user.verify_password(form.password.data) or not user.verify_pin(form.pin_key.data) or not user.verify_postcode(form.postcode.data):
            session['authentication_attempts'] += 1
            logger.warning('SECURITY - Invalid Log In Attempt [%s, %s]', form.email.data, request.remote_addr)

            if session.get('authentication_attempts') >= 3:
                flash(Markup('Number of incorrect login attempts exceeded. Please click <a href="/reset">here</a> to '
                             'reset.'))
                return render_template('users/login.html')

            flash('Login failed. Please check your email, password, and PIN. {} attempts remaining'.format(
                3 - session.get('authentication_attempts')))
            return render_template('users/login.html', form=form)
        else:
            # if user exists, password match and PIN verified
            login_user(user)

            # Log user login
            logger.warning('SECURITY - Log In Attempt [%s, %s, %s]', current_user.id, current_user.email,
                           request.remote_addr)

            user.last_successful_login = user.current_successful_login
            user.current_successful_login = request.remote_addr
            user.login_total += 1

            user.last_login = user.current_login
            user.current_login = datetime.now()

            db.session.commit()

            if current_user.role == 'admin':
                return redirect(url_for('admin.admin'))
            else:
                return redirect(url_for('lottery.lottery'))

    return render_template('users/login.html', form=form)


@users_blueprint.route('/reset')
def reset():
    session['authentication_attempts'] = 0
    return redirect(url_for('users.login'))


@users_blueprint.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logger.warning('SECURITY - Log Out [ID: %s, Email: %s, IP: %s]', current_user.id, current_user.email,
                       request.remote_addr)
    logout_user()
    return redirect(url_for('index'))


# view user account
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('users/account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)


# view user account
@users_blueprint.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    form = PasswordForm()

    if form.validate_on_submit():
        # Check if the current password matches the actual password
        if not current_user.verify_password(form.current_password.data):
            flash('Invalid current password. Please try again.')
            return render_template('users/update_password.html', form=form)

        # Check if the new password is the same as the current password
        if current_user.verify_password(form.new_password.data):
            flash('New password must be different from the current password.')
            return render_template('users/update_password.html', form=form)

        # Set the new password and commit changes
        current_user.password = form.new_password.data
        db.session.commit()
        flash('Password changed successfully!')

        return redirect(url_for('users.account'))

    return render_template('users/update_password.html', form=form)
