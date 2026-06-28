from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from Mini.models import Event, Booking, booking_to_dict, db

bookings_bp = Blueprint('bookings_bp', __name__)

@bookings_bp.route("/api/bookings", methods=["POST"])
@login_required
def create_booking():
    data = request.get_json() or {}
    event = Event.query.get_or_404(data["event_id"])

    # check seat limit
    confirmed_bookings = Booking.query.filter_by(
        event_id=event.id, status='confirmed'
    ).count()
    if confirmed_bookings >= event.capacity:
        return jsonify({"error": "This event is fully booked"}), 400

    # check duplicate booking
    existing = Booking.query.filter_by(
        user_id=current_user.id, event_id=event.id
    ).first()
    if existing:
        return jsonify({"error": "You have already booked this event"}), 400

    booking = Booking(user_id=current_user.id, event_id=event.id)
    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booked successfully"}), 201

@bookings_bp.route("/api/bookings", methods=["GET"])
@login_required
def all_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return jsonify([booking_to_dict(b) for b in bookings])

@bookings_bp.route("/api/bookings/<int:booking_id>/cancel", methods=["PATCH"])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    booking.status = 'cancelled'
    db.session.commit()
    return jsonify({"message": "Booking cancelled"})

@bookings_bp.route("/api/events/<int:event_id>/bookings")
@login_required
def event_bookings(event_id):
    bookings = Booking.query.filter_by(event_id=event_id).all()
    return jsonify([booking_to_dict(b) for b in bookings])

@bookings_bp.route("/bookings")
@login_required
def bookings_page():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("bookings.html", bookings=bookings)