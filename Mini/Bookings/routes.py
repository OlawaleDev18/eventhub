from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from Mini.models import Event, Booking, booking_to_dict, db
from Mini import mail
from flask_mail import Message

bookings_bp = Blueprint('bookings_bp', __name__)

def send_booking_confirmation(user, event):
    try:
        msg = Message(
            'Booking Confirmed — EventHub 🎟️',
            sender='twalexh@gmail.com',
            recipients=[user.email]
        )
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; background: #0f172a; color: #f1f5f9; padding: 30px; border-radius: 16px;">
            <h1 style="color: #38bdf8; text-align: center;">🎟️ Booking Confirmed!</h1>
            <p style="font-size: 16px;">Hi <strong>{user.username}</strong>,</p>
            <p>Your booking has been confirmed. Here are your event details:</p>
            <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #38bdf8; margin-top: 0;">{event.title}</h2>
                <p>📍 <strong>Location:</strong> {event.location}</p>
                <p>📅 <strong>Date:</strong> {event.date.strftime('%B %d, %Y at %I:%M %p')}</p>
                <p>🎯 <strong>Category:</strong> {event.category}</p>
                <p>📝 <strong>Description:</strong> {event.description}</p>
            </div>
            <p style="color: #94a3b8; font-size: 14px;">
                Please arrive on time. If you need to cancel your booking,
                you can do so from your bookings page on EventHub.
            </p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="https://eventhub-1-p9de.onrender.com/bookings"
                   style="background: linear-gradient(135deg, #38bdf8, #0ea5e9);
                          color: white; padding: 12px 30px; border-radius: 999px;
                          text-decoration: none; font-weight: bold;">
                    View My Bookings
                </a>
            </div>
            <p style="text-align: center; color: #64748b; font-size: 12px; margin-top: 30px;">
                EventHub — Book and manage events with ease.<br>
                If you did not make this booking, please ignore this email.
            </p>
        </div>
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Confirmation email error: {e}")


def send_cancellation_email(user, event):
    try:
        msg = Message(
            'Booking Cancelled — EventHub',
            sender='twalexh@gmail.com',
            recipients=[user.email]
        )
        msg.html = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; background: #0f172a; color: #f1f5f9; padding: 30px; border-radius: 16px;">
            <h1 style="color: #f87171; text-align: center;">❌ Booking Cancelled</h1>
            <p style="font-size: 16px;">Hi <strong>{user.username}</strong>,</p>
            <p>Your booking for the following event has been cancelled:</p>
            <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #f87171; margin-top: 0;">{event.title}</h2>
                <p>📅 <strong>Date:</strong> {event.date.strftime('%B %d, %Y at %I:%M %p')}</p>
                <p>📍 <strong>Location:</strong> {event.location}</p>
            </div>
            <p>If you cancelled by mistake you can rebook from the events page.</p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="https://eventhub-1-p9de.onrender.com/events/"
                   style="background: linear-gradient(135deg, #38bdf8, #0ea5e9);
                          color: white; padding: 12px 30px; border-radius: 999px;
                          text-decoration: none; font-weight: bold;">
                    Browse Events
                </a>
            </div>
            <p style="text-align: center; color: #64748b; font-size: 12px; margin-top: 30px;">
                EventHub — Book and manage events with ease.
            </p>
        </div>
        '''
        mail.send(msg)
    except Exception as e:
        print(f"Cancellation email error: {e}")


@bookings_bp.route("/api/bookings", methods=["POST"])
@login_required
def create_booking():
    data = request.get_json() or {}

    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"error": "Event ID is required"}), 400

    try:
        event_id = int(event_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid event ID"}), 400

    event = Event.query.get_or_404(event_id)

    confirmed_bookings = Booking.query.filter_by(
        event_id=event.id, status='confirmed'
    ).count()
    if confirmed_bookings >= event.capacity:
        return jsonify({"error": "Sorry, this event is fully booked"}), 400

    existing = Booking.query.filter_by(
        user_id=current_user.id, event_id=event.id
    ).first()
    if existing and existing.status == 'confirmed':
        return jsonify({"error": "You have already booked this event"}), 400

    booking = Booking(user_id=current_user.id, event_id=event.id)
    db.session.add(booking)
    db.session.commit()

    send_booking_confirmation(current_user, event)

    return jsonify({"message": "Booked successfully! A confirmation email has been sent."}), 201


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

    event = Event.query.get(booking.event_id)
    booking.status = 'cancelled'
    db.session.commit()

    send_cancellation_email(current_user, event)

    return jsonify({"message": "Booking cancelled successfully"})


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