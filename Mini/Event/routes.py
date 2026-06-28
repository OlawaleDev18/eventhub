from flask import Blueprint, request, jsonify, render_template
from Mini.models import Event, db, event_to_dict, Booking
from datetime import datetime
from flask_login import login_required, current_user

events_bp = Blueprint('events', __name__)

@events_bp.route("/api/events", methods=["POST"])
def create_events():
    data = request.get_json() or {}
    event = Event(
        title=data.get("title"),
        description=data.get("description"),
        location=data.get("location"),
        capacity=data.get("capacity"),
        category=data.get("category"),
        date=datetime.fromisoformat(data.get("date")),
        organiser_id=1
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event_to_dict(event)), 201

@events_bp.route("/api/events", methods=["GET"])
def all_events():
    events = Event.query.all()
    return jsonify([event_to_dict(e) for e in events])

@events_bp.route("/events/")
@login_required
def events_page():
    events = Event.query.all()
    booked_event_ids = []
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    booked_event_ids = [b.event_id for b in bookings]
    return render_template("events.html", events=events, booked_event_ids=booked_event_ids)


@events_bp.route("/api/admin/stats")
@login_required
def admin_stats():
    if not current_user.is_organiser:
        return jsonify({"error": "Unauthorized"}), 403
    
    from Mini.models import User, Event, Booking
    total_users = User.query.count()
    total_events = Event.query.count()
    total_bookings = Booking.query.count()
    confirmed = Booking.query.filter_by(status='confirmed').count()
    cancelled = Booking.query.filter_by(status='cancelled').count()
    
    return jsonify({
        "total_users": total_users,
        "total_events": total_events,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled
    })
