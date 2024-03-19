# IMPORTS
import random
from functools import wraps

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app import db, logger
from models import User, Draw
from users.forms import RegisterForm

# CONFIG
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                # log unauthorized access attempts
                logger.warning('SECURITY - Unauthorized Access Attempts [%s, %s, %s ,%s]', current_user.id, current_user.email, current_user.role, request.remote_addr)
                return render_template('errors.html', error_code="403", error_name="Forbidden Error"), 403
            return f(*args, **kwargs)

        return wrapped

    return wrapper


# VIEWS
# view admin homepage
@admin_blueprint.route('/admin')
@login_required
@requires_roles('admin')
def admin():
    return render_template('admin/admin.html', name=current_user.firstname)


#create a new winning draw
@admin_blueprint.route('/generate_winning_draw', methods=['POST'])
@login_required
@requires_roles('admin')
def generate_winning_draw():
    # get current winning draw
    current_winning_draw = Draw.query.filter_by(master_draw=True).first()
    lottery_round = 1

    # if a current winning draw exists
    if current_winning_draw:
        # update lottery round by 1
        lottery_round = current_winning_draw.lottery_round + 1

        #delete current winning draw
        db.session.delete(current_winning_draw)
        db.session.commit()

    #get new winning numbers for draw
    winning_numbers = random.sample(range(1, 60), 6)
    winning_numbers.sort()
    winning_numbers_string = ''
    for i in range(6):
        winning_numbers_string += str(winning_numbers[i]) + ''
    winning_numbers_string = winning_numbers_string[:1]

    # create a new draw object
    new_winning_draw = Draw(user_id=0, numbers=winning_numbers_string, master_draw=True, lottery_round=lottery_round, draw_key=current_user.draw_key)

    #add the new winning draw to the database
    db.session.add(new_winning_draw)
    db.session.commit()

    #render admin page
    flash("New winning draw %s added." % winning_numbers_string)
    return redirect(url_for('admin.admin'))


# view current winning draw
@admin_blueprint.route('/view_winning_draw', methods=['POST'])
@login_required
@requires_roles('admin')
def view_winning_draw():
    # get winning draw from DB
    current_winning_draw = Draw.query.filter_by(master_draw=True, been_played=False).first()

    # if a winning draw exists
    if current_winning_draw:

        current_winning_draw.view_numbers(current_user.draw_key)
        # re-render admin page with current winning draw and lottery round
        return render_template('admin/admin.html', winning_draw=current_winning_draw, name=current_user.firstname)

    # if no winning draw exists, rerender admin page
    flash("No valid winning draw exists. Please add new winning draw.")
    return redirect(url_for('admin.admin'))


# view lottery results and winners
@admin_blueprint.route('/run_lottery', methods=['POST'])
@login_required
@requires_roles('admin')
def run_lottery():
    # get current unplayed winning draw
    current_winning_draw = Draw.query.filter_by(master_draw=True, been_played=False).first()

    # if current unplayed winning draw exists
    if current_winning_draw:

        # get all unplayed user draws
        user_draws = Draw.query.filter_by(master_draw=False, been_played=False).all()
        results = []

        # if at least one unplayed user draw exists
        if user_draws:

            # update current winning draw as played
            current_winning_draw.been_played = True
            db.session.add(current_winning_draw)
            db.session.commit()

            # for each unplayed user draw
            for draw in user_draws:

                # get the owning user (instance/object)
                user = User.query.filter_by(id=draw.user_id).first()

                # if user draw matches current unplayed winning draw
                if draw.numbers == current_winning_draw.numbers:
                    # add details of winner to list of results
                    results.append((current_winning_draw.lottery_round, draw.numbers, draw.user_id, user.email))

                    # update draw as a winning draw (this will be used to highlight winning draws in the user's
                    # lottery page)
                    draw.matches_master = True

                # update draw as played
                draw.been_played = True

                # update draw with current lottery round
                draw.lottery_round = current_winning_draw.lottery_round

                # commit draw changes to DB
                db.session.add(draw)
                db.session.commit()

            # if no winners
            if len(results) == 0:
                flash("No winners.")

            return render_template('admin/admin.html', results=results, name=current_user.firstname)

        flash("No user draws entered.")
        return admin()

    # if current unplayed winning draw does not exist
    flash("Current winning draw expired. Add new winning draw for next round.")
    return redirect(url_for('admin.admin'))


# view all registered users
@admin_blueprint.route('/view_all_users', methods=['POST'])
@login_required
@requires_roles('admin')
def view_all_users():
    current_users = User.query.filter_by(role='user').all()

    return render_template('admin/admin.html', name=current_user.firstname, current_users=current_users)


# view last 10 log entries
@admin_blueprint.route('/logs', methods=['POST'])
@login_required
@requires_roles('admin')
def logs():
    with open("lottery.log", "r") as f:
        content = f.read().splitlines()[-10:]
        content.reverse()

    return render_template('admin/admin.html', logs=content, name=current_user.firstname)


@admin_blueprint.route('/view_user_activity', methods=['POST'])
@login_required
@requires_roles('admin')
def view_user_activity():
    return render_template('admin/admin.html', name=current_user.firstname, user_activity_logs=User.query.filter_by())


@admin_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.role == 'admin':
            # create a new user with the form data
            new_admin = User(email=form.email.data,
                             firstname=form.firstname.data,
                             lastname=form.lastname.data,
                             phone=form.phone.data,
                             postcode=form.postcode.data,
                             password=form.password.data,
                             role='admin')

            # add the new user to the database
            db.session.add(new_admin)
            db.session.commit()

            flash('New admin user registered successfully!', 'success')
            return redirect(url_for('admin.admin'))

        flash('You do not have permission to register a new admin user.', 'danger')
        return redirect(url_for('admin.admin'))
