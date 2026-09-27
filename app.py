import os
import io
import csv
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from flask import Flask, request, jsonify, render_template, Response, make_response
from database import init_db, get_db, row_to_dict, rows_to_dict_list
from seed_data import seed_database_if_empty

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))
app.config["JSON_SORT_KEYS"] = False

# Auto-initialize DB and seed if empty on app startup
init_db()
seed_database_if_empty()

@app.route("/health")
@app.route("/api/health")
def health():
    """Health check endpoint for Google Cloud Run container liveness."""
    return jsonify({
        "status": "healthy",
        "service": "PulseCare Clinic & Emergency Management System",
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "Administrative, appointment & emergency coordination portal. No medical diagnosis or treatment."
    })

@app.route("/")
def index():
    """Render the primary single-page application dashboard."""
    return render_template("index.html")

# ==========================================
# DASHBOARD & ANALYTICS APIS
# ==========================================

@app.route("/api/dashboard/stats")
def get_dashboard_stats():
    """Fetch aggregated clinic and emergency metrics."""
    today_str = date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Today's appointments by status
        cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", (today_str,))
        today_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ? AND status = 'Waiting'", (today_str,))
        waiting_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ? AND status = 'In-Consultation'", (today_str,))
        in_consult_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ? AND status = 'Completed'", (today_str,))
        completed_today = cursor.fetchone()["count"]

        # Total registered patients
        cursor.execute("SELECT COUNT(*) as count FROM patients")
        total_patients = cursor.fetchone()["count"]

        # Ambulances
        cursor.execute("SELECT COUNT(*) as count FROM ambulances WHERE status = 'Available'")
        available_ambulances = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM ambulances")
        total_ambulances = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM ambulance_requests WHERE status IN ('Pending', 'Dispatched', 'Transporting')")
        active_ambulance_requests = cursor.fetchone()["count"]

        # Blood emergencies
        cursor.execute("SELECT COUNT(*) as count FROM blood_requests WHERE status IN ('Urgent', 'In-Process')")
        urgent_blood_requests = cursor.fetchone()["count"]

        # Reminders pending today or overdue
        cursor.execute("SELECT COUNT(*) as count FROM followup_reminders WHERE status = 'Pending' AND reminder_date <= ?", (today_str,))
        pending_reminders = cursor.fetchone()["count"]

        # Appointments breakdown by specialty
        cursor.execute("""
            SELECT d.specialty, COUNT(a.id) as count
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            GROUP BY d.specialty
            ORDER BY count DESC
        """)
        specialty_breakdown = rows_to_dict_list(cursor.fetchall())

        # Appointments breakdown by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM appointments
            WHERE appointment_date = ?
            GROUP BY status
        """, (today_str,))
        status_breakdown = rows_to_dict_list(cursor.fetchall())

        # Blood stock totals across all banks
        cursor.execute("""
            SELECT 
                SUM(stock_a_pos) as "A+",
                SUM(stock_a_neg) as "A-",
                SUM(stock_b_pos) as "B+",
                SUM(stock_b_neg) as "B-",
                SUM(stock_ab_pos) as "AB+",
                SUM(stock_ab_neg) as "AB-",
                SUM(stock_o_pos) as "O+",
                SUM(stock_o_neg) as "O-"
            FROM blood_banks
        """)
        blood_totals_row = cursor.fetchone()
        blood_stock_summary = dict(blood_totals_row) if blood_totals_row else {}

        # Active emergency alerts
        cursor.execute("SELECT * FROM emergency_alerts WHERE status = 'Active' ORDER BY id DESC LIMIT 5")
        active_alerts = rows_to_dict_list(cursor.fetchall())

        # 7-day appointment trend
        past_7_days = [(date.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        trend_data = []
        for d in past_7_days:
            cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", (d,))
            trend_data.append({"date": d, "count": cursor.fetchone()["count"]})

        return jsonify({
            "today_total": today_total,
            "waiting_count": waiting_count,
            "in_consult_count": in_consult_count,
            "completed_today": completed_today,
            "total_patients": total_patients,
            "available_ambulances": available_ambulances,
            "total_ambulances": total_ambulances,
            "active_ambulance_requests": active_ambulance_requests,
            "urgent_blood_requests": urgent_blood_requests,
            "pending_reminders": pending_reminders,
            "specialty_breakdown": specialty_breakdown,
            "status_breakdown": status_breakdown,
            "blood_stock_summary": blood_stock_summary,
            "active_alerts": active_alerts,
            "trend_data": trend_data
        })

# ==========================================
# PATIENT MANAGEMENT APIS
# ==========================================

@app.route("/api/patients", methods=["GET"])
def get_patients():
    """Retrieve patient list with optional search query and blood group filter."""
    search = request.args.get("search", "").strip()
    blood_group = request.args.get("blood_group", "").strip()

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT p.*, 
                   COUNT(DISTINCT v.id) as total_visits,
                   MAX(v.visit_date) as last_visit_date
            FROM patients p
            LEFT JOIN visit_history v ON p.id = v.patient_id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (p.full_name LIKE ? OR p.phone LIKE ? OR p.patient_code LIKE ?)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        if blood_group:
            query += " AND p.blood_group = ?"
            params.append(blood_group)

        query += " GROUP BY p.id ORDER BY p.id DESC"
        cursor.execute(query, params)
        patients = rows_to_dict_list(cursor.fetchall())
        return jsonify(patients)

@app.route("/api/patients/<int:patient_id>", methods=["GET"])
def get_patient_profile(patient_id):
    """Retrieve comprehensive profile for a single patient including visits and reminders."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        patient = row_to_dict(cursor.fetchone())
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Past visits
        cursor.execute("""
            SELECT * FROM visit_history 
            WHERE patient_id = ? 
            ORDER BY visit_date DESC, id DESC
        """, (patient_id,))
        visits = rows_to_dict_list(cursor.fetchall())

        # Appointments
        cursor.execute("""
            SELECT a.*, d.name as doctor_name, d.specialty as doctor_specialty, d.room_number
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.time_slot ASC
        """, (patient_id,))
        appointments = rows_to_dict_list(cursor.fetchall())

        # Reminders
        cursor.execute("""
            SELECT * FROM followup_reminders 
            WHERE patient_id = ? 
            ORDER BY reminder_date DESC
        """, (patient_id,))
        reminders = rows_to_dict_list(cursor.fetchall())

        return jsonify({
            "patient": patient,
            "visits": visits,
            "appointments": appointments,
            "reminders": reminders
        })

@app.route("/api/patients", methods=["POST"])
def register_patient():
    """Register a new patient and generate a unique patient code."""
    data = request.json or {}
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()

    if not full_name or not phone:
        return jsonify({"error": "Full Name and Phone Number are required"}), 400

    age = data.get("age")
    try:
        age = int(age) if age else None
    except ValueError:
        age = None

    gender = data.get("gender", "Unspecified")
    email = data.get("email", "").strip()
    blood_group = data.get("blood_group", "").strip()
    emergency_contact_name = data.get("emergency_contact_name", "").strip()
    emergency_contact_phone = data.get("emergency_contact_phone", "").strip()
    address = data.get("address", "").strip()
    allergies = data.get("allergies", "").strip()
    pre_existing_conditions = data.get("pre_existing_conditions", "").strip()
    notes = data.get("notes", "").strip()

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Generate code
        cursor.execute("SELECT MAX(id) as max_id FROM patients")
        max_id = cursor.fetchone()["max_id"] or 0
        patient_code = f"PT-{datetime.now().year}-{str(max_id + 1).zfill(3)}"

        cursor.execute("""
            INSERT INTO patients (
                patient_code, full_name, age, gender, phone, email, blood_group,
                emergency_contact_name, emergency_contact_phone, address, allergies,
                pre_existing_conditions, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_code, full_name, age, gender, phone, email, blood_group,
            emergency_contact_name, emergency_contact_phone, address, allergies,
            pre_existing_conditions, notes
        ))
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM patients WHERE id = ?", (new_id,))
        new_patient = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Patient registered successfully",
            "patient": new_patient
        }), 201

@app.route("/api/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    """Update patient administrative details."""
    data = request.json or {}
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Patient not found"}), 404

        cursor.execute("""
            UPDATE patients SET
                full_name = COALESCE(?, full_name),
                age = COALESCE(?, age),
                gender = COALESCE(?, gender),
                phone = COALESCE(?, phone),
                email = COALESCE(?, email),
                blood_group = COALESCE(?, blood_group),
                emergency_contact_name = COALESCE(?, emergency_contact_name),
                emergency_contact_phone = COALESCE(?, emergency_contact_phone),
                address = COALESCE(?, address),
                allergies = COALESCE(?, allergies),
                pre_existing_conditions = COALESCE(?, pre_existing_conditions),
                notes = COALESCE(?, notes)
            WHERE id = ?
        """, (
            data.get("full_name"),
            data.get("age"),
            data.get("gender"),
            data.get("phone"),
            data.get("email"),
            data.get("blood_group"),
            data.get("emergency_contact_name"),
            data.get("emergency_contact_phone"),
            data.get("address"),
            data.get("allergies"),
            data.get("pre_existing_conditions"),
            data.get("notes"),
            patient_id
        ))

        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        updated = row_to_dict(cursor.fetchone())
        return jsonify({"message": "Patient updated successfully", "patient": updated})

# ==========================================
# DOCTOR DIRECTORY APIS
# ==========================================

@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    """Retrieve list of clinic physicians and specialties."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors ORDER BY name ASC")
        return jsonify(rows_to_dict_list(cursor.fetchall()))

# ==========================================
# APPOINTMENT BOOKING & SCHEDULING APIS
# ==========================================

@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    """Retrieve appointments with filters: date, status, doctor_id."""
    app_date = request.args.get("date", "").strip()
    status = request.args.get("status", "").strip()
    doctor_id = request.args.get("doctor_id", "").strip()

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT a.*, 
                   p.full_name as patient_name, p.phone as patient_phone, p.blood_group, p.patient_code, p.age as patient_age, p.gender as patient_gender,
                   d.name as doctor_name, d.specialty as doctor_specialty, d.room_number
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE 1=1
        """
        params = []

        if app_date and app_date != "all":
            query += " AND a.appointment_date = ?"
            params.append(app_date)

        if status and status != "all":
            query += " AND a.status = ?"
            params.append(status)

        if doctor_id and doctor_id != "all":
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)

        query += " ORDER BY a.appointment_date DESC, a.time_slot ASC, a.token_number ASC"
        cursor.execute(query, params)
        return jsonify(rows_to_dict_list(cursor.fetchall()))

@app.route("/api/appointments", methods=["POST"])
def book_appointment():
    """Book a new clinic appointment with conflict prevention and automatic token number generation."""
    data = request.json or {}
    patient_id = data.get("patient_id")
    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date", "").strip()
    time_slot = data.get("time_slot", "").strip()
    visit_type = data.get("visit_type", "General Consultation").strip()
    reason = data.get("reason", "").strip()
    notes = data.get("notes", "").strip()

    if not patient_id or not doctor_id or not appointment_date or not time_slot:
        return jsonify({"error": "Patient, Doctor, Appointment Date, and Time Slot are required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()

        # Check for scheduling slot conflict with the same doctor
        cursor.execute("""
            SELECT id FROM appointments 
            WHERE doctor_id = ? AND appointment_date = ? AND time_slot = ? AND status != 'Cancelled'
        """, (doctor_id, appointment_date, time_slot))
        conflict = cursor.fetchone()
        if conflict:
            return jsonify({
                "error": f"Doctor already has a confirmed appointment at {time_slot} on {appointment_date}. Please choose another time slot."
            }), 409

        # Generate sequential token for this date
        cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = ?", (appointment_date,))
        count_for_day = cursor.fetchone()["count"] + 1
        token_number = f"T-{str(count_for_day).zfill(2)}"

        # Generate appointment code
        cursor.execute("SELECT MAX(id) as max_id FROM appointments")
        max_id = cursor.fetchone()["max_id"] or 0
        appointment_code = f"APT-{datetime.now().year}-{str(max_id + 1).zfill(3)}"

        cursor.execute("""
            INSERT INTO appointments (
                appointment_code, patient_id, doctor_id, appointment_date,
                time_slot, visit_type, token_number, status, reason, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?, ?)
        """, (
            appointment_code, patient_id, doctor_id, appointment_date,
            time_slot, visit_type, token_number, reason, notes
        ))
        new_id = cursor.lastrowid

        cursor.execute("""
            SELECT a.*, p.full_name as patient_name, p.phone as patient_phone,
                   d.name as doctor_name, d.specialty as doctor_specialty, d.room_number
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.id = ?
        """, (new_id,))
        created = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Appointment scheduled successfully",
            "appointment": created
        }), 201

@app.route("/api/appointments/<int:appointment_id>/status", methods=["PUT"])
def update_appointment_status(appointment_id):
    """Update appointment state (Scheduled, Waiting, In-Consultation, Completed, Cancelled, No-Show)."""
    data = request.json or {}
    new_status = data.get("status", "").strip()

    valid_statuses = ["Scheduled", "Waiting", "In-Consultation", "Completed", "Cancelled", "No-Show"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        app_record = cursor.fetchone()
        if not app_record:
            return jsonify({"error": "Appointment not found"}), 404

        checked_in_at = app_record["checked_in_at"]
        completed_at = app_record["completed_at"]

        if new_status == "Waiting" and not checked_in_at:
            checked_in_at = now_str
        elif new_status == "Completed" and not completed_at:
            completed_at = now_str

        cursor.execute("""
            UPDATE appointments
            SET status = ?, checked_in_at = ?, completed_at = ?
            WHERE id = ?
        """, (new_status, checked_in_at, completed_at, appointment_id))

        cursor.execute("""
            SELECT a.*, p.full_name as patient_name, p.phone as patient_phone,
                   d.name as doctor_name, d.specialty as doctor_specialty, d.room_number
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.id = ?
        """, (appointment_id,))
        updated = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": f"Appointment status updated to '{new_status}'",
            "appointment": updated
        })

@app.route("/api/queue")
def get_live_queue():
    """Live Waiting Room Queue board data for clinic reception screen."""
    today_str = date.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.token_number, a.time_slot, a.status, a.visit_type,
                   p.full_name as patient_name, p.age, p.gender,
                   d.name as doctor_name, d.room_number, d.specialty
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.appointment_date = ? AND a.status IN ('Waiting', 'In-Consultation', 'Scheduled')
            ORDER BY 
                CASE a.status
                    WHEN 'In-Consultation' THEN 1
                    WHEN 'Waiting' THEN 2
                    WHEN 'Scheduled' THEN 3
                    ELSE 4
                END,
                a.token_number ASC
        """, (today_str,))
        queue_items = rows_to_dict_list(cursor.fetchall())
        return jsonify({
            "queue_date": today_str,
            "total_in_queue": len(queue_items),
            "queue": queue_items
        })

@app.route("/api/appointments/<int:appointment_id>/slip")
def get_appointment_slip(appointment_id):
    """Retrieve full appointment slip data formatted for printing or receipt generation."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, 
                   p.patient_code, p.full_name as patient_name, p.phone as patient_phone, p.age, p.gender, p.blood_group,
                   d.name as doctor_name, d.specialty, d.room_number, d.phone as doctor_phone
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.id = ?
        """, (appointment_id,))
        slip = row_to_dict(cursor.fetchone())
        if not slip:
            return jsonify({"error": "Appointment not found"}), 404

        slip["clinic_name"] = "PulseCare Health & Emergency Medical Center"
        slip["clinic_address"] = "48 100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru"
        slip["clinic_emergency_helpline"] = "+91 80 4099 1100 / 108"
        return jsonify(slip)

# ==========================================
# VISIT HISTORY & CONSULTATION LOGS
# ==========================================

@app.route("/api/visits", methods=["POST"])
def add_visit_record():
    """Log a completed clinical consultation / visit with administrative notes and follow-up date."""
    data = request.json or {}
    patient_id = data.get("patient_id")
    appointment_id = data.get("appointment_id")
    doctor_name = data.get("doctor_name", "").strip()
    department = data.get("department", "General Medicine").strip()
    visit_type = data.get("visit_type", "General Consultation").strip()
    chief_complaint = data.get("chief_complaint", "").strip()
    administrative_notes = data.get("administrative_notes", "").strip()
    follow_up_recommended_date = data.get("follow_up_recommended_date", "").strip()

    if not patient_id or not doctor_name:
        return jsonify({"error": "Patient and Doctor Name are required"}), 400

    today_str = date.today().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO visit_history (
                patient_id, appointment_id, visit_date, doctor_name, department,
                visit_type, chief_complaint, administrative_notes, follow_up_recommended_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, appointment_id, today_str, doctor_name, department,
            visit_type, chief_complaint, administrative_notes, follow_up_recommended_date
        ))
        visit_id = cursor.lastrowid

        # If appointment_id was provided, mark appointment as Completed
        if appointment_id:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE appointments SET status = 'Completed', completed_at = ?
                WHERE id = ?
            """, (now_str, appointment_id))

        # If follow-up date was specified, automatically generate a follow-up reminder
        reminder_created = False
        if follow_up_recommended_date:
            cursor.execute("SELECT full_name, phone FROM patients WHERE id = ?", (patient_id,))
            patient_info = cursor.fetchone()
            if patient_info:
                p_name = patient_info["full_name"]
                msg = f"Dear {p_name}, this is a follow-up review reminder from PulseCare Clinic with {doctor_name} scheduled around {follow_up_recommended_date}. Please contact us to confirm your time slot."
                cursor.execute("""
                    INSERT INTO followup_reminders (
                        patient_id, appointment_id, reminder_date, reason, status, channel, message_text
                    ) VALUES (?, ?, ?, ?, 'Pending', 'WhatsApp', ?)
                """, (patient_id, appointment_id, follow_up_recommended_date, f"Follow-up consultation with {doctor_name}", msg))
                reminder_created = True

        cursor.execute("SELECT * FROM visit_history WHERE id = ?", (visit_id,))
        created_visit = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Visit record added successfully",
            "visit": created_visit,
            "reminder_created": reminder_created
        }), 201

# ==========================================
# FOLLOW-UP REMINDERS & WHATSAPP ENGINE
# ==========================================

@app.route("/api/reminders", methods=["GET"])
def get_reminders():
    """Retrieve follow-up reminders with optional status and date filtering."""
    status = request.args.get("status", "").strip()
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT r.*, 
                   p.full_name as patient_name, p.phone as patient_phone, p.patient_code, p.blood_group
            FROM followup_reminders r
            JOIN patients p ON r.patient_id = p.id
            WHERE 1=1
        """
        params = []
        if status and status != "all":
            query += " AND r.status = ?"
            params.append(status)

        query += " ORDER BY r.reminder_date ASC, r.id DESC"
        cursor.execute(query, params)
        reminders = rows_to_dict_list(cursor.fetchall())

        # Build WhatsApp ready direct link for each reminder
        for rem in reminders:
            phone_clean = "".join([c for c in rem["patient_phone"] if c.isdigit()])
            if not phone_clean.startswith("91") and len(phone_clean) == 10:
                phone_clean = "91" + phone_clean
            text = rem["message_text"] or f"Hello {rem['patient_name']}, reminder for your healthcare follow-up at PulseCare Clinic."
            rem["whatsapp_link"] = f"https://wa.me/{phone_clean}?text={quote_plus(text)}"

        return jsonify(reminders)

@app.route("/api/reminders", methods=["POST"])
def create_reminder():
    """Create a manual follow-up reminder."""
    data = request.json or {}
    patient_id = data.get("patient_id")
    reminder_date = data.get("reminder_date", "").strip()
    reason = data.get("reason", "").strip()
    channel = data.get("channel", "WhatsApp").strip()
    message_text = data.get("message_text", "").strip()

    if not patient_id or not reminder_date or not reason:
        return jsonify({"error": "Patient, Reminder Date, and Reason are required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        if not message_text:
            cursor.execute("SELECT full_name FROM patients WHERE id = ?", (patient_id,))
            p = cursor.fetchone()
            p_name = p["full_name"] if p else "Patient"
            message_text = f"Dear {p_name}, this is a reminder from PulseCare Clinic regarding: {reason} on {reminder_date}."

        cursor.execute("""
            INSERT INTO followup_reminders (patient_id, reminder_date, reason, status, channel, message_text)
            VALUES (?, ?, ?, 'Pending', ?, ?)
        """, (patient_id, reminder_date, reason, channel, message_text))
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM followup_reminders WHERE id = ?", (new_id,))
        return jsonify({"message": "Reminder created successfully", "reminder": row_to_dict(cursor.fetchone())}), 201

@app.route("/api/reminders/<int:reminder_id>/send", methods=["POST"])
def mark_reminder_sent(reminder_id):
    """Mark reminder as dispatched with timestamp."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE followup_reminders
            SET status = 'Sent', sent_at = ?
            WHERE id = ?
        """, (now_str, reminder_id))

        cursor.execute("""
            SELECT r.*, p.full_name as patient_name, p.phone as patient_phone
            FROM followup_reminders r
            JOIN patients p ON r.patient_id = p.id
            WHERE r.id = ?
        """, (reminder_id,))
        updated = row_to_dict(cursor.fetchone())
        return jsonify({"message": "Reminder logged as Sent", "reminder": updated})

# ==========================================
# AMBULANCE FLEET & EMERGENCY DISPATCH APIS
# ==========================================

@app.route("/api/ambulances", methods=["GET"])
def get_ambulances():
    """Retrieve full ambulance fleet with real-time status and GPS coordinates."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ambulances ORDER BY status ASC, id ASC")
        return jsonify(rows_to_dict_list(cursor.fetchall()))

@app.route("/api/ambulances/<int:ambulance_id>/status", methods=["PUT"])
def update_ambulance_status(ambulance_id):
    """Update vehicle status: Available, Dispatched, On-Route, Maintenance."""
    data = request.json or {}
    status = data.get("status", "").strip()
    valid = ["Available", "Dispatched", "On-Route", "Maintenance"]
    if status not in valid:
        return jsonify({"error": f"Invalid status. Must be one of {valid}"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ambulances
            SET status = ?, last_updated = ?
            WHERE id = ?
        """, (status, now_str, ambulance_id))

        cursor.execute("SELECT * FROM ambulances WHERE id = ?", (ambulance_id,))
        return jsonify({"message": f"Ambulance updated to {status}", "ambulance": row_to_dict(cursor.fetchone())})

@app.route("/api/ambulances/request", methods=["POST"])
def submit_ambulance_request():
    """Submit an urgent ambulance dispatch request."""
    data = request.json or {}
    caller_name = data.get("caller_name", "").strip()
    caller_phone = data.get("caller_phone", "").strip()
    pickup_address = data.get("pickup_address", "").strip()
    destination_facility = data.get("destination_facility", "PulseCare Specialty Clinic & Daycare").strip()
    urgency_level = data.get("urgency_level", "High Urgency").strip()
    patient_name = data.get("patient_name", "").strip() or caller_name
    ambulance_type_needed = data.get("ambulance_type_needed", "Basic Life Support (BLS)").strip()
    notes = data.get("notes", "").strip()
    assigned_ambulance_id = data.get("assigned_ambulance_id")

    if not caller_name or not caller_phone or not pickup_address:
        return jsonify({"error": "Caller Name, Phone, and Pickup Address are required"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()

        # If no specific ambulance was assigned, pick the first available matching or general vehicle
        if not assigned_ambulance_id:
            cursor.execute("SELECT id FROM ambulances WHERE status = 'Available' ORDER BY id ASC LIMIT 1")
            avail = cursor.fetchone()
            if avail:
                assigned_ambulance_id = avail["id"]

        # Generate request code
        cursor.execute("SELECT MAX(id) as max_id FROM ambulance_requests")
        max_id = cursor.fetchone()["max_id"] or 0
        request_code = f"AMB-REQ-{8800 + max_id + 1}"

        status = "Dispatched" if assigned_ambulance_id else "Pending"
        dispatched_at = now_str if assigned_ambulance_id else None

        cursor.execute("""
            INSERT INTO ambulance_requests (
                request_code, caller_name, caller_phone, patient_name,
                pickup_address, destination_facility, urgency_level,
                ambulance_type_needed, assigned_ambulance_id, status,
                latitude, longitude, notes, dispatched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 12.9716, 77.6412, ?, ?)
        """, (
            request_code, caller_name, caller_phone, patient_name,
            pickup_address, destination_facility, urgency_level,
            ambulance_type_needed, assigned_ambulance_id, status,
            notes, dispatched_at
        ))
        req_id = cursor.lastrowid

        # Update the assigned ambulance status to Dispatched
        if assigned_ambulance_id:
            cursor.execute("UPDATE ambulances SET status = 'Dispatched', last_updated = ? WHERE id = ?", (now_str, assigned_ambulance_id))

        # Add an emergency alert
        cursor.execute("""
            INSERT INTO emergency_alerts (title, alert_type, severity, message, status)
            VALUES (?, 'Ambulance SOS', ?, ?, 'Active')
        """, (
            f"Ambulance Request {request_code}",
            "Critical" if "Critical" in urgency_level else "High",
            f"Ambulance requested for {patient_name} at {pickup_address}. Destination: {destination_facility}."
        ))

        cursor.execute("""
            SELECT r.*, a.vehicle_number, a.driver_name, a.driver_phone, a.ambulance_type
            FROM ambulance_requests r
            LEFT JOIN ambulances a ON r.assigned_ambulance_id = a.id
            WHERE r.id = ?
        """, (req_id,))
        created = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Ambulance request registered and dispatched",
            "request": created
        }), 201

@app.route("/api/ambulances/requests", methods=["GET"])
def get_ambulance_requests():
    """Retrieve all ambulance requests with vehicle and driver details."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, a.vehicle_number, a.driver_name, a.driver_phone, a.ambulance_type, a.current_location_name
            FROM ambulance_requests r
            LEFT JOIN ambulances a ON r.assigned_ambulance_id = a.id
            ORDER BY 
                CASE r.status
                    WHEN 'Pending' THEN 1
                    WHEN 'Dispatched' THEN 2
                    WHEN 'Transporting' THEN 3
                    ELSE 4
                END,
                r.id DESC
        """)
        return jsonify(rows_to_dict_list(cursor.fetchall()))

@app.route("/api/ambulances/requests/<int:req_id>/status", methods=["PUT"])
def update_ambulance_request_status(req_id):
    """Update status of an ambulance request: Dispatched, Transporting, Completed, Cancelled."""
    data = request.json or {}
    new_status = data.get("status", "").strip()
    assigned_ambulance_id = data.get("assigned_ambulance_id")

    valid = ["Pending", "Dispatched", "Transporting", "Completed", "Cancelled"]
    if new_status not in valid:
        return jsonify({"error": f"Invalid status. Must be one of {valid}"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ambulance_requests WHERE id = ?", (req_id,))
        req = cursor.fetchone()
        if not req:
            return jsonify({"error": "Ambulance request not found"}), 404

        amb_id = assigned_ambulance_id or req["assigned_ambulance_id"]
        completed_at = now_str if new_status in ["Completed", "Cancelled"] else req["completed_at"]
        dispatched_at = now_str if (new_status == "Dispatched" and not req["dispatched_at"]) else req["dispatched_at"]

        cursor.execute("""
            UPDATE ambulance_requests
            SET status = ?, assigned_ambulance_id = ?, completed_at = ?, dispatched_at = ?
            WHERE id = ?
        """, (new_status, amb_id, completed_at, dispatched_at, req_id))

        # Free the ambulance back to Available if completed or cancelled
        if new_status in ["Completed", "Cancelled"] and amb_id:
            cursor.execute("UPDATE ambulances SET status = 'Available', last_updated = ? WHERE id = ?", (now_str, amb_id))
        elif new_status == "Dispatched" and amb_id:
            cursor.execute("UPDATE ambulances SET status = 'Dispatched', last_updated = ? WHERE id = ?", (now_str, amb_id))

        cursor.execute("SELECT * FROM ambulance_requests WHERE id = ?", (req_id,))
        return jsonify({"message": f"Request updated to {new_status}", "request": row_to_dict(cursor.fetchone())})

# ==========================================
# BLOOD BANK & SOS REQUIREMENTS APIS
# ==========================================

@app.route("/api/blood/banks", methods=["GET"])
def get_blood_banks():
    """Retrieve directory of blood banks and inventory matrix."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blood_banks ORDER BY distance_km ASC")
        return jsonify(rows_to_dict_list(cursor.fetchall()))

@app.route("/api/blood/search", methods=["GET"])
def search_blood():
    """Search blood availability across local blood banks by group and location."""
    blood_group = request.args.get("blood_group", "").strip().upper()
    city = request.args.get("city", "").strip()

    group_to_column = {
        "A+": "stock_a_pos",
        "A-": "stock_a_neg",
        "B+": "stock_b_pos",
        "B-": "stock_b_neg",
        "AB+": "stock_ab_pos",
        "AB-": "stock_ab_neg",
        "O+": "stock_o_pos",
        "O-": "stock_o_neg"
    }

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blood_banks ORDER BY distance_km ASC")
        banks = rows_to_dict_list(cursor.fetchall())

        results = []
        for bank in banks:
            if blood_group and blood_group in group_to_column:
                col = group_to_column[blood_group]
                units = bank.get(col, 0)
                bank["searched_group"] = blood_group
                bank["available_units"] = units
                bank["in_stock"] = units > 0
            results.append(bank)

        # Also get compatible donors
        cursor.execute("SELECT * FROM blood_donors WHERE blood_group = ? AND is_available = 1", (blood_group,))
        donors = rows_to_dict_list(cursor.fetchall())

        return jsonify({
            "blood_group": blood_group,
            "banks": results,
            "compatible_donors": donors
        })

@app.route("/api/blood/requests", methods=["GET"])
def get_blood_requests():
    """Retrieve all active blood emergency requests."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT br.*, bb.name as matched_bank_name, bb.contact_phone as matched_bank_phone
            FROM blood_requests br
            LEFT JOIN blood_banks bb ON br.matched_bank_id = bb.id
            ORDER BY 
                CASE br.status
                    WHEN 'Urgent' THEN 1
                    WHEN 'In-Process' THEN 2
                    ELSE 3
                END,
                br.id DESC
        """)
        return jsonify(rows_to_dict_list(cursor.fetchall()))

@app.route("/api/blood/request", methods=["POST"])
def submit_blood_request():
    """Post an urgent SOS blood requirement."""
    data = request.json or {}
    patient_name = data.get("patient_name", "").strip()
    blood_group = data.get("blood_group", "").strip().upper()
    units_required = data.get("units_required")
    hospital_name = data.get("hospital_name", "").strip()
    contact_person = data.get("contact_person", "").strip()
    contact_phone = data.get("contact_phone", "").strip()
    urgency = data.get("urgency", "Within 4 Hours").strip()
    notes = data.get("notes", "").strip()

    if not patient_name or not blood_group or not units_required or not hospital_name or not contact_phone:
        return jsonify({"error": "Patient Name, Blood Group, Units, Hospital, and Contact Phone are required"}), 400

    try:
        units_required = int(units_required)
    except ValueError:
        return jsonify({"error": "Units must be an integer"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) as max_id FROM blood_requests")
        max_id = cursor.fetchone()["max_id"] or 0
        request_code = f"BLD-REQ-{400 + max_id + 1}"

        cursor.execute("""
            INSERT INTO blood_requests (
                request_code, patient_name, blood_group, units_required,
                hospital_name, contact_person, contact_phone, urgency,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Urgent', ?)
        """, (
            request_code, patient_name, blood_group, units_required,
            hospital_name, contact_person, contact_phone, urgency, notes
        ))
        new_id = cursor.lastrowid

        # Insert emergency alert
        cursor.execute("""
            INSERT INTO emergency_alerts (title, alert_type, severity, message, status)
            VALUES (?, 'Critical Blood Shortage', 'Critical', ?, 'Active')
        """, (
            f"Urgent Blood Need: {blood_group} ({units_required} Units)",
            f"{units_required} units of {blood_group} needed urgently for {patient_name} at {hospital_name}. Contact: {contact_phone}"
        ))

        cursor.execute("SELECT * FROM blood_requests WHERE id = ?", (new_id,))
        return jsonify({
            "message": "Blood requirement posted successfully",
            "blood_request": row_to_dict(cursor.fetchone())
        }), 201

@app.route("/api/blood/requests/<int:req_id>/status", methods=["PUT"])
def update_blood_request_status(req_id):
    """Update status of a blood request: Urgent, In-Process, Fulfilled, Cancelled."""
    data = request.json or {}
    status = data.get("status", "").strip()
    matched_bank_id = data.get("matched_bank_id")

    valid = ["Urgent", "In-Process", "Fulfilled", "Cancelled"]
    if status not in valid:
        return jsonify({"error": f"Invalid status. Must be one of {valid}"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE blood_requests
            SET status = ?, matched_bank_id = COALESCE(?, matched_bank_id)
            WHERE id = ?
        """, (status, matched_bank_id, req_id))

        cursor.execute("SELECT * FROM blood_requests WHERE id = ?", (req_id,))
        return jsonify({"message": f"Blood request status updated to {status}", "blood_request": row_to_dict(cursor.fetchone())})

@app.route("/api/blood/donors", methods=["GET", "POST"])
def handle_donors():
    """List or register voluntary blood donors."""
    if request.method == "POST":
        data = request.json or {}
        full_name = data.get("full_name", "").strip()
        blood_group = data.get("blood_group", "").strip().upper()
        phone = data.get("phone", "").strip()
        city = data.get("city", "Bengaluru").strip()

        if not full_name or not blood_group or not phone:
            return jsonify({"error": "Full Name, Blood Group, and Phone are required"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO blood_donors (full_name, blood_group, phone, city, last_donated_date, is_available)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (full_name, blood_group, phone, city, date.today().strftime("%Y-%m-%d")))
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM blood_donors WHERE id = ?", (new_id,))
            return jsonify({"message": "Donor registered successfully", "donor": row_to_dict(cursor.fetchone())}), 201
    else:
        blood_group = request.args.get("blood_group", "").strip().upper()
        with get_db() as conn:
            cursor = conn.cursor()
            if blood_group:
                cursor.execute("SELECT * FROM blood_donors WHERE blood_group = ? ORDER BY id DESC", (blood_group,))
            else:
                cursor.execute("SELECT * FROM blood_donors ORDER BY id DESC")
            return jsonify(rows_to_dict_list(cursor.fetchall()))

# ==========================================
# NEARBY HEALTHCARE FACILITIES APIS
# ==========================================

@app.route("/api/facilities", methods=["GET"])
def get_facilities():
    """Retrieve nearby hospitals, trauma centers, and pharmacies with distance and ICU capacity."""
    facility_type = request.args.get("type", "").strip()
    search = request.args.get("search", "").strip()

    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM nearby_facilities WHERE 1=1"
        params = []

        if facility_type and facility_type != "all":
            query += " AND facility_type LIKE ?"
            params.append(f"%{facility_type}%")

        if search:
            query += " AND (name LIKE ? OR address LIKE ? OR specialties LIKE ?)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        query += " ORDER BY distance_km ASC"
        cursor.execute(query, params)
        return jsonify(rows_to_dict_list(cursor.fetchall()))

# ==========================================
# EMERGENCY TRIAGE & SOS COORDINATION
# ==========================================

@app.route("/api/emergency/sos", methods=["POST"])
def submit_emergency_triage():
    """Unified fast emergency triage: creates ambulance request and emergency broadcast simultaneously."""
    data = request.json or {}
    emergency_type = data.get("emergency_type", "General Medical Emergency").strip()
    patient_name = data.get("patient_name", "").strip()
    caller_phone = data.get("caller_phone", "").strip()
    pickup_address = data.get("pickup_address", "").strip()
    urgency_level = data.get("urgency_level", "Critical / Life-Threatening").strip()
    destination = data.get("destination", "Manipal Hospital (Old Airport Road)").strip()
    notes = data.get("notes", "").strip()

    if not patient_name or not caller_phone or not pickup_address:
        return jsonify({"error": "Patient Name, Contact Phone, and Pickup Location are required"}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()

        # Find nearest available ambulance
        cursor.execute("SELECT id, vehicle_number, driver_name, driver_phone FROM ambulances WHERE status = 'Available' LIMIT 1")
        amb = cursor.fetchone()
        assigned_amb_id = amb["id"] if amb else None

        # Create ambulance request
        cursor.execute("SELECT MAX(id) as max_id FROM ambulance_requests")
        max_id = cursor.fetchone()["max_id"] or 0
        req_code = f"SOS-EMG-{9900 + max_id + 1}"

        status = "Dispatched" if assigned_amb_id else "Pending"
        cursor.execute("""
            INSERT INTO ambulance_requests (
                request_code, caller_name, caller_phone, patient_name,
                pickup_address, destination_facility, urgency_level,
                ambulance_type_needed, assigned_ambulance_id, status,
                latitude, longitude, notes, dispatched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Advanced Life Support (ALS)', ?, ?, 12.9716, 77.6412, ?, ?)
        """, (
            req_code, patient_name, caller_phone, patient_name,
            pickup_address, destination, urgency_level,
            assigned_amb_id, status, f"EMERGENCY SOS: {emergency_type}. {notes}",
            now_str if assigned_amb_id else None
        ))
        amb_req_id = cursor.lastrowid

        if assigned_amb_id:
            cursor.execute("UPDATE ambulances SET status = 'Dispatched', last_updated = ? WHERE id = ?", (now_str, assigned_amb_id))

        # Create Emergency Alert
        cursor.execute("""
            INSERT INTO emergency_alerts (title, alert_type, severity, message, status)
            VALUES (?, 'Emergency SOS Triage', 'Critical', ?, 'Active')
        """, (
            f"URGENT SOS: {patient_name} - {emergency_type}",
            f"Immediate emergency response initiated for {patient_name}. Location: {pickup_address}. Destination: {destination}. Assigned Unit: {amb['vehicle_number'] if amb else 'Pending Unit Dispatch'}."
        ))

        return jsonify({
            "message": "Emergency SOS broadcast initiated and ambulance dispatched!",
            "sos_code": req_code,
            "ambulance_assigned": dict(amb) if amb else None,
            "status": status
        }), 201

# ==========================================
# DATA EXPORT APIS (ADMINISTRATIVE COMPLIANCE)
# ==========================================

@app.route("/api/export/appointments.csv")
def export_appointments_csv():
    """Export clinic appointments to CSV for reporting."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.appointment_code, a.token_number, a.appointment_date, a.time_slot, a.status,
                   p.patient_code, p.full_name as patient_name, p.phone as patient_phone,
                   d.name as doctor_name, d.specialty
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            ORDER BY a.appointment_date DESC, a.time_slot ASC
        """)
        rows = cursor.fetchall()

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["Appointment Code", "Token", "Date", "Time Slot", "Status", "Patient Code", "Patient Name", "Phone", "Doctor", "Specialty"])
        for r in rows:
            cw.writerow([r["appointment_code"], r["token_number"], r["appointment_date"], r["time_slot"], r["status"], r["patient_code"], r["patient_name"], r["patient_phone"], r["doctor_name"], r["specialty"]])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=clinic_appointments.csv"
        output.headers["Content-type"] = "text/csv"
        return output

@app.route("/api/export/patients.csv")
def export_patients_csv():
    """Export patient directory to CSV."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT patient_code, full_name, age, gender, phone, email, blood_group, emergency_contact_name, emergency_contact_phone, address, allergies FROM patients ORDER BY id ASC")
        rows = cursor.fetchall()

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["Patient Code", "Full Name", "Age", "Gender", "Phone", "Email", "Blood Group", "Emergency Contact", "Emergency Phone", "Address", "Allergies"])
        for r in rows:
            cw.writerow([r["patient_code"], r["full_name"], r["age"], r["gender"], r["phone"], r["email"], r["blood_group"], r["emergency_contact_name"], r["emergency_contact_phone"], r["address"], r["allergies"]])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=patient_directory.csv"
        output.headers["Content-type"] = "text/csv"
        return output

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Production ready host binding for local and container environments
    print(f"[INFO] Starting PulseCare Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

