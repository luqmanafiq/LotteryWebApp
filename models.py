import pyotp
import bcrypt
from app import db, app
from flask_login import UserMixin
from datetime import datetime
from cryptography.fernet import Fernet


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information.
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    # User information
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='user')
    pin_key = db.Column(db.String(32), nullable=False, default=pyotp.random_base32())
    postcode = db.Column(db.String(10), nullable=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    current_login = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    current_successful_login = db.Column(db.String(15))
    last_successful_login = db.Column(db.String(15))
    login_total = db.Column(db.Integer, default=0)
    draw_key = db.Column(db.BLOB, nullable=False, default=Fernet.generate_key())

    # Define the relationship to Draw
    draws = db.relationship('Draw')

    def get_2fa_uri(self):
        return str(pyotp.totp.TOTP(self.pin_key).provisioning_uri(
            name=self.email,
            issuer_name='CSC2031 Lottery'))

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def verify_pin(self, pin):
        totp = pyotp.TOTP(self.pin_key)
        return totp.verify(pin)

    def verify_postcode(self, postcode):
        return self.postcode == postcode

    def __init__(self, email, firstname, lastname, phone, password, postcode, role):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.phone = phone
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role
        self.postcode = postcode
        self.registered_on = datetime.now()
        self.current_login = None
        self.last_login = None
        self.current_successful_login = None
        self.last_successful_login = None
        self.login_total = 0


def encrypt(data, key):
    f = Fernet(key)
    encrypted_data = f.encrypt(bytes(str(data), 'utf-8'))
    return encrypted_data.decode('utf-8')


def decrypt(data, draw_key):
    return Fernet(draw_key).decrypt(data).decode('utf-8')


class Draw(db.Model):
    __tablename__ = 'draws'

    id = db.Column(db.Integer, primary_key=True)

    # ID of user who submitted draw
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # 6 draw numbers submitted
    numbers = db.Column(db.String(100), nullable=False)

    # Draw has already been played (can only play draw once)
    been_played = db.Column(db.BOOLEAN, nullable=False, default=False)

    # Draw matches with master draw created by admin (True = draw is a winner)
    matches_master = db.Column(db.BOOLEAN, nullable=False, default=False)

    # True = draw is master draw created by admin. User draws are matched to master draw
    master_draw = db.Column(db.BOOLEAN, nullable=False)

    # Lottery round that draw is used
    lottery_round = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id, numbers, master_draw, lottery_round, draw_key):
        self.user_id = user_id
        self.numbers = encrypt(numbers, draw_key)
        self.been_played = False
        self.matches_master = False
        self.master_draw = master_draw
        self.lottery_round = lottery_round

    def view_numbers(self, draw_key):
        self.numbers = decrypt(self.numbers, draw_key)


def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(email='admin@email.com',
                     password='Admin1!',
                     firstname='Alice',
                     lastname='Jones',
                     phone='0191-123-4567',
                     postcode='NE2 4LB',
                     role='admin')

        db.session.add(admin)
        db.session.commit()
