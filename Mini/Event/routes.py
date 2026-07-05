from flask import Blueprint, request, jsonify, render_template
from Mini.models import Event, db, event_to_dict, Booking
from datetime import datetime
from flask_login import login_required, current_user

events_bp = Blueprint('events', __name__)

@events_bp.route("/api/events", methods=["POST"])
def create_events():
    data = request.get_json() or {}

    # validate required fields
    title       = data.get("title", "").strip()
    description = data.get("description", "").strip()
    location    = data.get("location", "").strip()
    category    = data.get("category", "").strip()
    date        = data.get("date")
    capacity    = data.get("capacity")

    if not title:
        return jsonify({"error": "Event title is required"}), 400

    if not description:
        return jsonify({"error": "Event description is required"}), 400

    if not location:
        return jsonify({"error": "Event location is required"}), 400

    if not category:
        return jsonify({"error": "Event category is required"}), 400

    if not date:
        return jsonify({"error": "Event date is required"}), 400

    if not capacity or int(capacity) < 1:
        return jsonify({"error": "Capacity must be at least 1"}), 400

    if len(title) > 100:
        return jsonify({"error": "Title must not exceed 100 characters"}), 400

    try:
        parsed_date = datetime.fromisoformat(date)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS"}), 400

    event = Event(
        title=title,
        description=description,
        location=location,
        capacity=int(capacity),
        category=category,
        date=parsed_date,
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


@events_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if not current_user.is_organiser:
        return jsonify({"error": "Unauthorized"}), 403

    from Mini.models import User, Event, Booking

    # stats
    total_users    = User.query.count()
    total_events   = Event.query.count()
    total_bookings = Booking.query.count()
    confirmed      = Booking.query.filter_by(status='confirmed').count()
    cancelled      = Booking.query.filter_by(status='cancelled').count()

    # all events with their booking counts
    events = Event.query.all()
    events_data = []
    for event in events:
        confirmed_count = Booking.query.filter_by(
            event_id=event.id, status='confirmed'
        ).count()
        cancelled_count = Booking.query.filter_by(
            event_id=event.id, status='cancelled'
        ).count()
        slots_left = event.capacity - confirmed_count
        events_data.append({
            "event": event,
            "confirmed": confirmed_count,
            "cancelled": cancelled_count,
            "slots_left": slots_left,
            "full": slots_left <= 0
        })

    # all registered users
    users = User.query.filter_by(is_organiser=False).all()

    # recent bookings — last 10
    recent_bookings = Booking.query.order_by(
        Booking.booked_at.desc()
    ).limit(10).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_events=total_events,
        total_bookings=total_bookings,
        confirmed=confirmed,
        cancelled=cancelled,
        events_data=events_data,
        users=users,
        recent_bookings=recent_bookings
    )


# keep the API version too for Thunderclient access
@events_bp.route("/api/admin/stats")
@login_required
def admin_stats():
    if not current_user.is_organiser:
        return jsonify({"error": "Unauthorized"}), 403

    from Mini.models import User, Event, Booking
    total_users    = User.query.count()
    total_events   = Event.query.count()
    total_bookings = Booking.query.count()
    confirmed      = Booking.query.filter_by(status='confirmed').count()
    cancelled      = Booking.query.filter_by(status='cancelled').count()

    return jsonify({
        "total_users": total_users,
        "total_events": total_events,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled
    })
