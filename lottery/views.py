# IMPORTS
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import make_transient
from cryptography.fernet import Fernet
from app import db
from lottery.forms import DrawForm
from models import Draw, encrypt

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
def lottery():
    return render_template('lottery/lottery.html', name=current_user.firstname)


# view all draws that have not been played
@lottery_blueprint.route('/create_draw', methods=['POST'])
@login_required
def create_draw():
    form = DrawForm()

    if form.validate_on_submit():
        submitted_numbers = [
            form.number1.data,
            form.number2.data,
            form.number3.data,
            form.number4.data,
            form.number5.data,
            form.number6.data
        ]

        # check if there are 6 numbers submitted
        if len(submitted_numbers) != 6:
            flash('Please submit exactly 6 numbers.')
            return redirect(url_for('lottery.lottery'))

        # check if all numbers submitted are 1-60
        if not all(1 <= num <= 60 for num in submitted_numbers):
            flash('All numbers must be between 1 and 60.')
            return redirect(url_for('lottery.lottery'))

        # Generate a new encryption key for drawing numbers
        draw_key = Fernet.generate_key()

        # Use the generated key to encrypt the lottery numbers
        new_draw = Draw(user_id=current_user.id, numbers=encrypt(submitted_numbers, draw_key), master_draw=False,
                        lottery_round=0, draw_key=draw_key)

        # Add the new draw to the database
        db.session.add(new_draw)
        db.session.commit()

        # re-render lottery.page
        flash(f'Draw {" ".join(map(str, submitted_numbers))} submitted.')
        return redirect(url_for('lottery.lottery'))

    return render_template('lottery/lottery.html', name=current_user.firstname, form=form)


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(been_played=False, user_id=current_user.id).all()

    # decrypting check draws
    for draw in playable_draws:
        make_transient(draw)
        draw.view_numbers(current_user.draw_key)

    # if playable draws exist
    if len(playable_draws) != 0:
        # re-render lottery page with playable draws
        return render_template('lottery/lottery.html', playable_draws=playable_draws)
    else:
        flash('No playable draws.')
        return redirect(url_for('lottery.lottery'))


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(been_played=True, user_id=current_user.id).all()

    # decrypting check draws
    for draw in played_draws:
        make_transient(draw)
        draw.view_numbers(current_user.draw_key)

    # if played draws exist
    if len(played_draws) != 0:
        return render_template('lottery/lottery.html', results=played_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return redirect(url_for('lottery.lottery'))


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
def play_again():
    Draw.query.filter_by(been_played=True, master_draw=False, user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()

    flash("All played draws deleted.")
    return redirect(url_for('lottery.lottery'))
