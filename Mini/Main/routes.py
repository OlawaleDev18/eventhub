from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from Mini.models import Event, User
from Mini import db, bcrypt, mail
from flask_mail import Message

main_bp = Blueprint('main_bp', __name__)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        'EventHub - Password Reset Request',
        sender='twalexh@gmail.com',
        recipients=[user.email]
    )
    msg.body = f'''Hello {user.username},

You requested a password reset for your EventHub account.

Click the link below to reset your password:
{url_for('main_bp.reset_token', token=token, _external=True)}

This link expires in 30 minutes.

If you did not request this, simply ignore this email.

EventHub Team
'''
    mail.send(msg)

@main_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@main_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.dashboard"))
    return render_template("home.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    event_count = Event.query.count()
    return render_template("dashboard.html", event_count=event_count)

@main_bp.route("/logout", methods=["GET"])
def logout_page():
    return render_template("login.html")

@main_bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)
        flash('If an account with that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('main_bp.login_page'))

    return render_template('reset_request.html')

@main_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That link is invalid or has expired.', 'warning')
        return redirect(url_for('main_bp.reset_request'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_token.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('main_bp.login_page'))

    return render_template('reset_token.html')