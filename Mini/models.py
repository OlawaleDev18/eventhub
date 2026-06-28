from Mini import db, login_manager , app
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_organiser = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, max_age=1800):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=max_age)['user_id']
        except:
            return None
        return User.query.get(user_id)

def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    organiser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bookings = db.relationship('Booking', backref='event', lazy=True)

def event_to_dict(event):
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date.isoformat() if event.date else None,
        "capacity": event.capacity,
        "location": event.location,
        "category": event.category,
        "organiser_id": event.organiser_id
    }

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

def booking_to_dict(booking):
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "event_id": booking.event_id,
        "status": booking.status,
        "booked_at": booking.booked_at.isoformat()
    }