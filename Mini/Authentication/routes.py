from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from Mini.models import User, user_to_dict
from Mini import db, bcrypt
from flask_login import login_user, logout_user, login_required , current_user

Authentication_bp = Blueprint('Authentication_bp', __name__)

@Authentication_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    user = User(
        username=data["username"],
        email=data["email"],
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
    user = User.query.filter_by(email=data.get("email")).first()
    if user and bcrypt.check_password_hash(user.password, data.get("password")):
        login_user(user)
        return redirect(url_for("main_bp.dashboard"))
    return jsonify({"error": "Invalid email or password"}), 401

@Authentication_bp.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main_bp.login_page"))


