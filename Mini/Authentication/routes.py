from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from Mini.models import User, user_to_dict
from Mini import db, bcrypt
from flask_login import login_user, logout_user, login_required, current_user
import re

Authentication_bp = Blueprint('Authentication_bp', __name__)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(pattern, email)

def is_strong_password(password):
    return len(password) >= 8

def sanitize(text):
    if text:
        return text.strip()
    return text

@Authentication_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    username = sanitize(data.get("username"))
    email    = sanitize(data.get("email"))
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400

    if len(username) > 20:
        return jsonify({"error": "Username must not exceed 20 characters"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Please enter a valid email address"}), 400

    if not is_strong_password(password):
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "This username is already taken"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        is_organiser=data.get("is_organiser", False)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"}), 201

@Authentication_bp.route("/api/register", methods=["GET"])
def all_register():
    registers = User.query.all()
    return jsonify([user_to_dict(d) for d in registers])

@Authentication_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email    = sanitize(data.get("email"))
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Please enter a valid email address"}), 400

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for("main_bp.dashboard"))

    return jsonify({"error": "Invalid email or password"}), 401

@Authentication_bp.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main_bp.login_page"))

@Authentication_bp.route("/api/register/<int:id>", methods=["DELETE"])
def delete_register(id):
    deleting= User.query.get_or_404(id)
    db.session.delete(deleting)
    db.session.commit()
    return jsonify({"message": "Register deleted"})