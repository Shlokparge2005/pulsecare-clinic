from datetime import datetime, date, timedelta
from database import get_db

def seed_database_if_empty():
    """Seeds the database with rich, realistic clinic and emergency coordination data if tables are empty."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
        if cursor.fetchone()["count"] > 0:
            return  # Already seeded
        
        print("[INFO] Seeding database with realistic clinic and emergency coordination data...")

        # 1. Doctors
        doctors = [
            ("Dr. Rajesh Sharma", "General Medicine & Family Physician", "+91 98111 22334", "dr.sharma@pulsecare.local", "Mon, Tue, Wed, Thu, Fri, Sat", "Room 101"),
            ("Dr. Ananya Sen", "Pediatrics & Child Health", "+91 98222 33445", "dr.sen@pulsecare.local", "Mon, Tue, Wed, Fri", "Room 102"),
            ("Dr. Vikram Malhotra", "Orthopedics & Joint Care", "+91 98333 44556", "dr.malhotra@pulsecare.local", "Tue, Thu, Sat", "Room 103"),
            ("Dr. Priya Desai", "Obstetrics & Gynecology", "+91 98444 55667", "dr.desai@pulsecare.local", "Mon, Wed, Fri", "Room 104"),
            ("Dr. Tariq Khan", "ENT & Head-Neck Specialist", "+91 98555 66778", "dr.khan@pulsecare.local", "Mon, Thu, Sat", "Room 105"),
            ("Dr. Sunita Rao", "Dermatology & Skin Wellness", "+91 98666 77889", "dr.rao@pulsecare.local", "Wed, Sat", "Room 106")
        ]
        cursor.executemany("""
            INSERT INTO doctors (name, specialty, phone, email, available_days, room_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, doctors)

        # 2. Patients
        patients = [
            ("PT-2026-001", "Arjun Patel", 34, "Male", "+91 98765 43210", "arjun.p@example.com", "O+", "Meera Patel (Spouse)", "+91 98765 43211", "Flat 402, Green Glen Layout, Bellandur", "Penicillin", "Mild Hypertension", "Corporate employee, regular evening visits"),
            ("PT-2026-002", "Deepa Nair", 28, "Female", "+91 91234 56789", "deepa.n@example.com", "B+", "Karthik Nair (Brother)", "+91 91234 56780", "12, 4th Cross, Indiranagar", "Sulfa drugs", "None", "Asthma history during winter season"),
            ("PT-2026-003", "Ramesh Kumar Gupta", 62, "Male", "+91 99887 76655", "ramesh.gupta@example.com", "A+", "Sunita Gupta (Wife)", "+91 99887 76650", "House 88, Sector 14, HSR Layout", "Aspirin", "Type-2 Diabetes, Dyslipidemia", "Senior citizen, requires wheelchair assistance"),
            ("PT-2026-004", "Fatima Zahra", 19, "Female", "+91 97654 32109", "fatima.z@example.com", "AB+", "Mohd. Zahra (Father)", "+91 97654 32100", "23/B Mosque Road, Frazer Town", "None", "None", "College student, annual general checkup"),
            ("PT-2026-005", "Suresh Reddy", 45, "Male", "+91 96543 21098", "suresh.r@example.com", "O-", "Kavita Reddy (Wife)", "+91 96543 21090", "Plot 7, Lake View Enclave, Koramangala", "None", "Mild Cervical Spondylosis", "IT professional, frequent neck stiffness"),
            ("PT-2026-006", "Aarav Sharma", 6, "Male", "+91 98111 99887", "parent.sharma@example.com", "A-", "Neha Sharma (Mother)", "+91 98111 99880", "Villa 12, Palm Meadows, Whitefield", "Dust mites", "Seasonal Bronchitis", "Pediatric patient, booster vaccines pending"),
            ("PT-2026-007", "Lakshmi Sundaram", 54, "Female", "+91 94433 22110", "lakshmi.s@example.com", "B-", "Venkatesh S (Son)", "+91 94433 22119", "Flat 101, Shanti Niketan, Malleshwaram", "Latex", "Hypothyroidism", "Routine thyroid panel review"),
            ("PT-2026-008", "David Fernandes", 41, "Male", "+91 93210 98765", "david.f@example.com", "AB-", "Maria Fernandes (Sister)", "+91 93210 98760", "45 St. Mark's Road, Ashok Nagar", "Ibuprofen", "Hypertension", "Executive checkup follow-up")
        ]
        cursor.executemany("""
            INSERT INTO patients (patient_code, full_name, age, gender, phone, email, blood_group, emergency_contact_name, emergency_contact_phone, address, allergies, pre_existing_conditions, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patients)

        today_str = date.today().strftime("%Y-%m-%d")
        tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        # 3. Appointments
        appointments = [
            ("APT-2026-101", 1, 1, today_str, "09:30 AM - 10:00 AM", "General Consultation", "T-01", "Completed", "Fever and mild body aches for 2 days", "Vitals normal. Advised hydration & rest.", "2026-09-27 09:25:00", "2026-09-27 09:55:00"),
            ("APT-2026-102", 2, 2, today_str, "10:00 AM - 10:30 AM", "Follow-up", "T-02", "In-Consultation", "Child persistent dry cough at night", "Evaluating chest congestion", "2026-09-27 09:50:00", None),
            ("APT-2026-103", 3, 1, today_str, "10:30 AM - 11:00 AM", "Routine Checkup", "T-03", "Waiting", "Quarterly blood sugar & BP management", "Patient in waiting area", "2026-09-27 10:20:00", None),
            ("APT-2026-104", 4, 4, today_str, "11:30 AM - 12:00 PM", "Consultation", "T-04", "Waiting", "Abdominal cramps and fatigue", "Tokens called once", "2026-09-27 11:15:00", None),
            ("APT-2026-105", 5, 3, today_str, "02:00 PM - 02:30 PM", "Consultation", "T-05", "Scheduled", "Severe lower back discomfort after lifting", "Requested ergonomic advice", None, None),
            ("APT-2026-106", 6, 2, today_str, "03:30 PM - 04:00 PM", "Vaccination", "T-06", "Scheduled", "MMR booster dose due", "Vaccine batch verified in stock", None, None),
            ("APT-2026-107", 7, 5, tomorrow_str, "10:00 AM - 10:30 AM", "Follow-up", "T-07", "Scheduled", "Sinus pressure and morning headache", "Pre-booked slot", None, None),
            ("APT-2026-108", 8, 1, tomorrow_str, "11:00 AM - 11:30 AM", "Consultation", "T-08", "Scheduled", "Follow-up BP readings review", "Brought 7-day home BP log", None, None),
            ("APT-2026-109", 1, 1, yesterday_str, "04:00 PM - 04:30 PM", "General Consultation", "T-09", "Completed", "Initial review for seasonal viral symptoms", "Advised laboratory blood counts", "2026-09-26 15:50:00", "2026-09-26 16:25:00")
        ]
        cursor.executemany("""
            INSERT INTO appointments (appointment_code, patient_id, doctor_id, appointment_date, time_slot, visit_type, token_number, status, reason, notes, checked_in_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, appointments)

        # 4. Visit History
        visits = [
            (1, 1, today_str, "Dr. Rajesh Sharma", "General Medicine", "General Consultation", "Fever and mild body aches for 2 days", "Administered paracetamol test dose; instructed to monitor temp every 6 hrs. Blood tests prescribed.", (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")),
            (3, 3, (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"), "Dr. Rajesh Sharma", "General Medicine", "Routine Checkup", "Quarterly diabetes checkup", "HbA1c was 6.8%. Continued existing metformin regimen. Advised dietary reduction in refined carbohydrates.", today_str),
            (5, 5, (date.today() - timedelta(days=14)).strftime("%Y-%m-%d"), "Dr. Vikram Malhotra", "Orthopedics", "Consultation", "Mild cervical strain", "X-ray showed no disc herniation. Recommended physiotherapy exercises and posture brace.", today_str),
            (6, 6, (date.today() - timedelta(days=60)).strftime("%Y-%m-%d"), "Dr. Ananya Sen", "Pediatrics", "Vaccination", "Routine pediatric developmental checkup", "Milestones appropriate for age. Height and weight in 65th percentile.", today_str)
        ]
        cursor.executemany("""
            INSERT INTO visit_history (patient_id, appointment_id, visit_date, doctor_name, department, visit_type, chief_complaint, administrative_notes, follow_up_recommended_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, visits)

        # 5. Follow-up Reminders
        reminders = [
            (1, 1, (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "Review CBC blood test results and temperature chart", "Pending", None, "WhatsApp", "Dear Arjun Patel, this is a follow-up reminder from PulseCare Clinic. Please submit your blood test reports for Dr. Rajesh Sharma's review."),
            (3, 3, today_str, "Quarterly HbA1c review and fasting glucose verification", "Pending", None, "WhatsApp", "Dear Ramesh Kumar Gupta, your quarterly diabetes follow-up is scheduled today with Dr. Rajesh Sharma. Please bring your morning fasting log."),
            (5, 5, (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"), "Check neck stiffness improvement with physiotherapy", "Pending", None, "WhatsApp", "Dear Suresh Reddy, gentle reminder to share your physiotherapy progress update with Dr. Vikram Malhotra."),
            (6, 6, today_str, "Booster dose MMR vaccination confirmation", "Sent", "2026-09-27 08:30:00", "WhatsApp", "Dear Neha Sharma, Aarav's MMR booster vaccination appointment is scheduled for this afternoon at PulseCare Clinic.")
        ]
        cursor.executemany("""
            INSERT INTO followup_reminders (patient_id, appointment_id, reminder_date, reason, status, sent_at, channel, message_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, reminders)

        # 6. Ambulances (Fleet)
        # Latitudes/Longitudes around Bangalore central coordinates (12.9716, 77.5946)
        ambulances = [
            ("AMB-KA-01-E-1008", "Advanced Life Support (ALS)", "Ramesh Gowda", "+91 98450 11223", "PulseCare Station 1 (Indiranagar)", 12.9784, 77.6408, "Available", "Ventilator, Defibrillator, Multipara Monitor, Oxygen Cylinders, Suction Unit"),
            ("AMB-KA-01-E-2015", "Basic Life Support (BLS)", "K. Manjunath", "+91 98450 22334", "Koramangala 80ft Road Junction", 12.9352, 77.6245, "Available", "Automated External Defibrillator (AED), First Aid, Splints, O2 Delivery, Stretcher"),
            ("AMB-KA-05-E-3042", "Advanced Life Support (ALS)", "Syed Irfan", "+91 98450 33445", "Outer Ring Road (Bellandur EcoSpace)", 12.9260, 77.6835, "Dispatched", "ICU Ventilator, Infusion Pumps, Syringe Pumps, Pulse Oximeter, Emergency Drug Kit"),
            ("AMB-KA-03-E-4019", "Patient Transport (PTS)", "V. Anand", "+91 98450 44556", "Whitefield Main Road (ITPB)", 12.9866, 77.7348, "Available", "Wheelchair ramp, Basic O2, Spine board, Pulse meter, First response kit"),
            ("AMB-KA-04-E-5120", "Neonatal & Pediatric Transport", "Girish Kumar", "+91 98450 55667", "Old Airport Road / Manipal Hub", 12.9592, 77.6534, "On-Route", "Transport Incubator, Micro-Ventilator, Pediatric Monitors, O2 Hoods"),
            ("AMB-KA-02-E-6218", "Basic Life Support (BLS)", "P. Chetan", "+91 98450 66778", "Malleshwaram 18th Cross", 13.0031, 77.5645, "Maintenance", "Routine calibration & oxygen refill check")
        ]
        cursor.executemany("""
            INSERT INTO ambulances (vehicle_number, ambulance_type, driver_name, driver_phone, current_location_name, latitude, longitude, status, equipment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ambulances)

        # 7. Ambulance Requests
        amb_requests = [
            ("AMB-REQ-8801", "Pooja Hegde", "+91 97412 88990", "Dinesh Hegde (Elderly)", "Flat 304, Prestige Ozone, Whitefield", "Manipal Hospital Whitefield", "Critical / Life-Threatening", "Advanced Life Support (ALS)", 3, "Dispatched", 12.9860, 77.7300, "Severe acute chest pain radiating to left arm. Oxygen administered on dispatch call.", "2026-09-27 10:14:00", None),
            ("AMB-REQ-8802", "Sunil Verma", "+91 99160 44332", "Aditya Verma (Age 22)", "Sarjapur Signal near Shell Petrol Pump", "St. John's Medical College Hospital", "High Urgency", "Basic Life Support (BLS)", 2, "Transporting", 12.9250, 77.6490, "Two-wheeler collision injury. Conscious, left knee and shoulder trauma.", "2026-09-27 09:40:00", None),
            ("AMB-REQ-8803", "Meenakshi Sundaram", "+91 94480 77123", "Raghavan S (Age 74)", "14, 5th Main, Defence Colony, Indiranagar", "PulseCare Specialty Clinic & Daycare", "Moderate / Transfer", "Patient Transport (PTS)", None, "Pending", 12.9750, 77.6380, "Post-surgery routine transfer to clinic for wound dressing and catheter change.", None, None)
        ]
        cursor.executemany("""
            INSERT INTO ambulance_requests (request_code, caller_name, caller_phone, patient_name, pickup_address, destination_facility, urgency_level, ambulance_type_needed, assigned_ambulance_id, status, latitude, longitude, notes, dispatched_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, amb_requests)

        # 8. Blood Banks
        blood_banks = [
            ("PulseCare Central Blood Bank & Component Lab", "100ft Road, HAL 2nd Stage, Indiranagar", "Bengaluru", "+91 80 2521 9900", "24/7", 12.9716, 77.6412, 1.2, 18, 4, 22, 5, 9, 3, 28, 7),
            ("Red Cross Regional Blood Centre", "26 Red Cross Bhawan, Race Course Road", "Bengaluru", "+91 80 2226 8456", "24/7", 12.9830, 77.5850, 4.8, 25, 6, 30, 4, 12, 2, 40, 9),
            ("Victoria Hospital Blood Bank & Trauma Center", "K.R. Market Fort Area", "Bengaluru", "+91 80 2670 1150", "24/7", 12.9620, 77.5750, 6.1, 14, 2, 19, 3, 7, 1, 22, 4),
            ("Manipal Comprehensive Blood Bank", "98 HAL Old Airport Road, Kodihalli", "Bengaluru", "+91 80 2502 4444", "24/7", 12.9590, 77.6530, 3.4, 20, 5, 24, 6, 11, 4, 35, 8),
            ("Rotary TTK Blood Bank", "New Thippasandra Main Road, HAL 3rd Stage", "Bengaluru", "+91 80 2528 7903", "08:00 AM - 10:00 PM", 12.9740, 77.6590, 2.7, 12, 3, 15, 2, 5, 2, 18, 3)
        ]
        cursor.executemany("""
            INSERT INTO blood_banks (name, address, city, contact_phone, operating_hours, latitude, longitude, distance_km, stock_a_pos, stock_a_neg, stock_b_pos, stock_b_neg, stock_ab_pos, stock_ab_neg, stock_o_pos, stock_o_neg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, blood_banks)

        # 9. Blood Requests
        blood_requests = [
            ("BLD-REQ-401", "Kiran Mazumdar", "O-", 2, "St. Philomena's Hospital", "Dr. Anthony D'Souza", "+91 98451 90812", "Immediate / Trauma", "Urgent", 1, "Emergency surgery scheduled for gastrointestinal arterial bleeding. Rare O-ve units needed urgently."),
            ("BLD-REQ-402", "Praveen Chandra", "B-", 3, "Manipal Hospital Old Airport Rd", "Staff Nurse Shilpa", "+91 98452 33411", "Within 4 Hours", "In-Process", 4, "Platelet and packed RBC requirement for dengue fever thrombocytopenia patient."),
            ("BLD-REQ-403", "Sumitra Devi", "AB-", 1, "Bowring & Lady Curzon Hospital", "Dr. Harish K", "+91 98453 77622", "Within 24 Hours", "Urgent", None, "Elective orthopedic hip arthroplasty scheduled tomorrow morning. AB-ve reserve unit required.")
        ]
        cursor.executemany("""
            INSERT INTO blood_requests (request_code, patient_name, blood_group, units_required, hospital_name, contact_person, contact_phone, urgency, status, matched_bank_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, blood_requests)

        # 10. Blood Donors
        donors = [
            ("Rahul Nair", "O-", "+91 99001 12233", "Bengaluru", "2026-05-10", 1),
            ("Naveen Teja", "O+", "+91 99002 23344", "Bengaluru", "2026-06-15", 1),
            ("Rohit Bansal", "AB-", "+91 99003 34455", "Bengaluru", "2026-04-20", 1),
            ("Pooja Chandran", "A+", "+91 99004 45566", "Bengaluru", "2026-07-02", 1),
            ("Simran Kaur", "B-", "+91 99005 56677", "Bengaluru", "2026-05-28", 1),
            ("Tanmay Joshi", "B+", "+91 99006 67788", "Bengaluru", "2026-06-25", 1),
            ("Farhan Akhtar", "A-", "+91 99007 78899", "Bengaluru", "2026-05-18", 1),
            ("Geeta Menon", "AB+", "+91 99008 89900", "Bengaluru", "2026-07-14", 1)
        ]
        cursor.executemany("""
            INSERT INTO blood_donors (full_name, blood_group, phone, city, last_donated_date, is_available)
            VALUES (?, ?, ?, ?, ?, ?)
        """, donors)

        # 11. Nearby Healthcare Facilities
        facilities = [
            ("PulseCare Multi-Specialty Primary Care Clinic", "24/7 Emergency Clinic", "48 100 Feet Road, HAL 2nd Stage, Indiranagar", "+91 80 4099 1100", 0.0, 4, 1, 12.9716, 77.6412, "Family Practice, Daycare ICU, Minor OT, ECG, X-Ray, Pharmacy", "Open 24/7"),
            ("Manipal Hospital (Old Airport Road)", "Multispecialty Hospital", "98 HAL Old Airport Road, Kodihalli", "+91 80 2502 4444", 3.2, 28, 1, 12.9592, 77.6534, "Level 1 Trauma Center, Cath Lab, Neuro ICU, 24/7 Emergency", "Open 24/7"),
            ("St. John's Medical College Hospital", "Government / Teaching Hospital", "Sarjapur Road, John Nagar, Koramangala", "+91 80 2206 5000", 5.8, 35, 1, 12.9345, 77.6189, "Comprehensive Emergency, Burns Unit, Pediatrics, Blood Center", "Open 24/7"),
            ("Bowring & Lady Curzon Hospital", "Government Tertiary Hospital", "Lady Curzon Road, Tasker Town, Shivaji Nagar", "+91 80 2559 1325", 5.1, 18, 1, 12.9825, 77.6035, "General Surgery, Orthopedics, Trauma Ward, Anti-Rabies Clinic", "Open 24/7"),
            ("Chinmaya Mission Hospital", "Community Multispecialty Hospital", "CMH Road, Defence Colony, Indiranagar", "+91 80 2528 0461", 1.4, 8, 1, 12.9785, 77.6432, "General Medicine, Cardiology, Emergency Triage, Dialysis", "Open 24/7"),
            ("Apollo 24/7 Pharmacy & First Aid Center", "24/7 Pharmacy", "12 CMH Road, Near Indiranagar Metro", "+91 80 2520 1199", 0.8, 0, 0, 12.9775, 77.6445, "24/7 Emergency Medications, Insulin Cold Chain, Oxygen Delivery", "Open 24/7"),
            ("Medall Clumax Diagnostics & Imaging", "Diagnostic Lab", "14th Main, HAL 2nd Stage, Indiranagar", "+91 80 4115 8899", 1.1, 0, 0, 12.9695, 77.6385, "128 Slice CT, MRI, Digital X-Ray, Automated Pathology Lab", "06:30 AM - 10:30 PM")
        ]
        cursor.executemany("""
            INSERT INTO nearby_facilities (name, facility_type, address, emergency_phone, distance_km, icu_beds_available, ambulance_service_available, latitude, longitude, specialties, open_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, facilities)

        # 12. Emergency Alerts
        alerts = [
            ("Critical Blood Shortage: O-Negative Needed", "Critical Blood Shortage", "Critical", "Urgent request for 2 units of O- Negative blood at St. Philomena's Hospital for emergency trauma surgical stabilization. Contact blood bank immediately.", "Active"),
            ("Ambulance Unit AMB-03 Dispatched to Whitefield", "Ambulance SOS", "High", "Ambulance AMB-KA-05-E-3042 dispatched to Bellandur EcoSpace road for cardiac stabilization transit to Manipal Whitefield.", "Active"),
            ("Notice: Administrative System Scope", "System Notice", "Info", "PulseCare operates strictly as an administrative scheduling, ambulance dispatch, and blood emergency coordination portal. It does not provide medical diagnoses or treatment advice.", "Active")
        ]
        cursor.executemany("""
            INSERT INTO emergency_alerts (title, alert_type, severity, message, status)
            VALUES (?, ?, ?, ?, ?)
        """, alerts)

        print("[SUCCESS] Database seeding completed successfully!")
