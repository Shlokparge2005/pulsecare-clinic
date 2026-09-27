import sqlite3
import os
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = "/tmp/clinic_system.db"
else:
    DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "data", "clinic_system.db"))


def get_db_connection():
    """Create a thread-safe database connection returning sqlite3.Row objects."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db():
    """Context manager for safe database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database tables and indexes."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT NOT NULL,
                email TEXT,
                blood_group TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                address TEXT,
                allergies TEXT,
                pre_existing_conditions TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Doctors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                available_days TEXT,
                room_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_code TEXT UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                appointment_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                visit_type TEXT DEFAULT 'General Consultation',
                token_number TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                reason TEXT,
                notes TEXT,
                checked_in_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Visit history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
                visit_date TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                department TEXT NOT NULL,
                visit_type TEXT NOT NULL,
                chief_complaint TEXT,
                administrative_notes TEXT,
                follow_up_recommended_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Follow-up reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS followup_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
                reminder_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                sent_at TIMESTAMP,
                channel TEXT DEFAULT 'WhatsApp',
                message_text TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ambulances fleet table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ambulances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_number TEXT UNIQUE NOT NULL,
                ambulance_type TEXT NOT NULL,
                driver_name TEXT NOT NULL,
                driver_phone TEXT NOT NULL,
                current_location_name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                status TEXT DEFAULT 'Available',
                equipment TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ambulance requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ambulance_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_code TEXT UNIQUE NOT NULL,
                caller_name TEXT NOT NULL,
                caller_phone TEXT NOT NULL,
                patient_name TEXT,
                pickup_address TEXT NOT NULL,
                destination_facility TEXT NOT NULL,
                urgency_level TEXT NOT NULL,
                ambulance_type_needed TEXT,
                assigned_ambulance_id INTEGER REFERENCES ambulances(id) ON DELETE SET NULL,
                status TEXT DEFAULT 'Pending',
                latitude REAL,
                longitude REAL,
                notes TEXT,
                dispatched_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Blood banks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blood_banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                contact_phone TEXT NOT NULL,
                operating_hours TEXT DEFAULT '24/7',
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                distance_km REAL DEFAULT 2.0,
                stock_a_pos INTEGER DEFAULT 12,
                stock_a_neg INTEGER DEFAULT 4,
                stock_b_pos INTEGER DEFAULT 16,
                stock_b_neg INTEGER DEFAULT 3,
                stock_ab_pos INTEGER DEFAULT 8,
                stock_ab_neg INTEGER DEFAULT 2,
                stock_o_pos INTEGER DEFAULT 22,
                stock_o_neg INTEGER DEFAULT 6,
                last_stock_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Blood requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blood_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_code TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                units_required INTEGER NOT NULL,
                hospital_name TEXT NOT NULL,
                contact_person TEXT NOT NULL,
                contact_phone TEXT NOT NULL,
                urgency TEXT NOT NULL,
                status TEXT DEFAULT 'Urgent',
                matched_bank_id INTEGER REFERENCES blood_banks(id) ON DELETE SET NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Voluntary blood donors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blood_donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                phone TEXT NOT NULL,
                city TEXT NOT NULL,
                last_donated_date TEXT,
                is_available INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Nearby healthcare facilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nearby_facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                facility_type TEXT NOT NULL,
                address TEXT NOT NULL,
                emergency_phone TEXT NOT NULL,
                distance_km REAL NOT NULL,
                icu_beds_available INTEGER DEFAULT 0,
                ambulance_service_available INTEGER DEFAULT 1,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                specialties TEXT,
                open_status TEXT DEFAULT 'Open 24/7'
            )
        """)

        # Emergency alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_code ON patients(patient_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ambulances_status ON ambulances(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blood_requests_status ON blood_requests(status)")

def row_to_dict(row):
    """Convert an SQLite Row object to a standard Python dictionary."""
    if row is None:
        return None
    return dict(row)

def rows_to_dict_list(rows):
    """Convert a list of SQLite Row objects to a list of dicts."""
    return [dict(r) for r in rows]
