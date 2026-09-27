import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_endpoint(name, method, url, payload=None, expected_status=200):
    full_url = f"{BASE_URL}{url}"
    try:
        if method == "GET":
            r = requests.get(full_url)
        elif method == "POST":
            r = requests.post(full_url, json=payload)
        elif method == "PUT":
            r = requests.put(full_url, json=payload)
        
        status_match = (r.status_code == expected_status)
        symbol = "[PASS]" if status_match else "[FAIL]"
        print(f"{symbol} {name} -> Status: {r.status_code} (Expected {expected_status})")
        if not status_match:
            print(f"       Response: {r.text[:200]}")
            return False, r
        return True, r
    except Exception as e:
        print(f"[FAIL] {name} -> Exception: {e}")
        return False, None

def run_all_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE PULSECARE TEST SUITE")
    print("=" * 60)

    passed = 0
    total = 0

    # 1. Health check
    total += 1
    ok, r = test_endpoint("Health Check (/health)", "GET", "/health")
    if ok: passed += 1

    # 2. Main Page HTML
    total += 1
    ok, r = test_endpoint("Web App Main Page (/)", "GET", "/")
    if ok and "PulseCare" in r.text: 
        passed += 1
        print("       Verified: PulseCare brand HTML loaded")

    # 3. Dashboard Stats
    total += 1
    ok, r = test_endpoint("Dashboard Stats (/api/dashboard/stats)", "GET", "/api/dashboard/stats")
    if ok:
        data = r.json()
        print(f"       Total Patients: {data.get('total_patients')}, Available Ambulances: {data.get('available_ambulances')}")
        passed += 1

    # 4. Doctors List
    total += 1
    ok, r = test_endpoint("Doctors Directory (/api/doctors)", "GET", "/api/doctors")
    if ok and len(r.json()) > 0:
        passed += 1
        print(f"       Found {len(r.json())} practicing doctors")

    # 5. Patient Registration
    total += 1
    new_patient_payload = {
        "full_name": "Test User Vikram",
        "phone": "+91 99999 88888",
        "age": 30,
        "gender": "Male",
        "blood_group": "O+",
        "emergency_contact_name": "Rita Vikram",
        "emergency_contact_phone": "+91 99999 77777",
        "address": "Indiranagar 12th Main, Bengaluru",
        "allergies": "None",
        "pre_existing_conditions": "None",
        "notes": "Automated verification test user"
    }
    ok, r = test_endpoint("Register Patient (/api/patients)", "POST", "/api/patients", new_patient_payload, 201)
    new_patient_id = None
    if ok:
        new_patient_id = r.json()["patient"]["id"]
        passed += 1
        print(f"       Registered patient code: {r.json()['patient']['patient_code']}")

    # 6. Patient Search
    total += 1
    ok, r = test_endpoint("Search Patient (/api/patients?search=Vikram)", "GET", "/api/patients?search=Vikram")
    if ok and len(r.json()) > 0:
        passed += 1

    # 7. Patient Profile & History
    total += 1
    ok, r = test_endpoint(f"Patient Profile (/api/patients/{new_patient_id or 1})", "GET", f"/api/patients/{new_patient_id or 1}")
    if ok: passed += 1

    # 8. Book Appointment
    total += 1
    apt_payload = {
        "patient_id": new_patient_id or 1,
        "doctor_id": 1,
        "appointment_date": "2026-10-01",
        "time_slot": "11:30 AM - 12:00 PM",
        "visit_type": "General Consultation",
        "reason": "Test routine health checkup",
        "notes": "Verified by test suite"
    }
    ok, r = test_endpoint("Book Appointment (/api/appointments)", "POST", "/api/appointments", apt_payload, 201)
    apt_id = None
    if ok:
        apt_id = r.json()["appointment"]["id"]
        passed += 1
        print(f"       Assigned Token: {r.json()['appointment']['token_number']}")

    # 9. Test Double-Booking Conflict Prevention
    total += 1
    ok, r = test_endpoint("Slot Conflict Detection", "POST", "/api/appointments", apt_payload, 409)
    if ok:
        passed += 1
        print(f"       Conflict successfully prevented: {r.json().get('error')}")

    # 10. Update Appointment Status
    total += 1
    ok, r = test_endpoint(f"Update Appointment Status to Waiting (/api/appointments/{apt_id or 1}/status)", "PUT", f"/api/appointments/{apt_id or 1}/status", {"status": "Waiting"})
    if ok: passed += 1

    # 11. Appointment Slip
    total += 1
    ok, r = test_endpoint(f"Appointment Slip (/api/appointments/{apt_id or 1}/slip)", "GET", f"/api/appointments/{apt_id or 1}/slip")
    if ok: passed += 1

    # 12. Add Clinical Visit Log & Auto-Reminder
    total += 1
    visit_payload = {
        "patient_id": new_patient_id or 1,
        "appointment_id": apt_id,
        "doctor_name": "Dr. Rajesh Sharma",
        "department": "General Medicine",
        "visit_type": "General Consultation",
        "chief_complaint": "Seasonal allergy symptoms",
        "administrative_notes": "Prescribed antihistamines. Follow-up review scheduled in 7 days.",
        "follow_up_recommended_date": "2026-10-08"
    }
    ok, r = test_endpoint("Add Clinical Visit Log (/api/visits)", "POST", "/api/visits", visit_payload, 201)
    if ok:
        passed += 1
        print("       Visit logged and automated follow-up reminder triggered!")

    # 13. Ambulances List
    total += 1
    ok, r = test_endpoint("Ambulances Fleet (/api/ambulances)", "GET", "/api/ambulances")
    if ok and len(r.json()) > 0: passed += 1

    # 14. Request Ambulance SOS
    total += 1
    amb_req_payload = {
        "caller_name": "Emergency Test Caller",
        "caller_phone": "+91 98450 99999",
        "patient_name": "Elderly Trauma Patient",
        "pickup_address": "88 Koramangala 4th Block",
        "urgency_level": "Critical / Life-Threatening",
        "destination_facility": "Manipal Hospital (Old Airport Road)",
        "ambulance_type_needed": "Advanced Life Support (ALS)"
    }
    ok, r = test_endpoint("Submit Ambulance Request (/api/ambulances/request)", "POST", "/api/ambulances/request", amb_req_payload, 201)
    if ok:
        passed += 1
        print(f"       Ambulance dispatched: {r.json()['request']['vehicle_number']}")

    # 15. Blood Banks & Search
    total += 1
    ok, r = test_endpoint("Blood Bank Directory (/api/blood/banks)", "GET", "/api/blood/banks")
    if ok and len(r.json()) > 0: passed += 1

    # 16. Blood Group Stock Search
    total += 1
    ok, r = test_endpoint("Search Blood Group O- (/api/blood/search?blood_group=O-)", "GET", "/api/blood/search?blood_group=O-")
    if ok: passed += 1

    # 17. Post Blood Requirement SOS
    total += 1
    blood_req_payload = {
        "patient_name": "Critical Trauma Patient",
        "blood_group": "O-",
        "units_required": 2,
        "hospital_name": "Victoria Hospital",
        "contact_person": "Duty Sister Mary",
        "contact_phone": "+91 80 2670 1150",
        "urgency": "Immediate / Trauma",
        "notes": "Emergency blood transfusion"
    }
    ok, r = test_endpoint("Post Blood Requirement SOS (/api/blood/request)", "POST", "/api/blood/request", blood_req_payload, 201)
    if ok: passed += 1

    # 18. Nearby Healthcare Facilities
    total += 1
    ok, r = test_endpoint("Nearby Facilities (/api/facilities)", "GET", "/api/facilities")
    if ok and len(r.json()) > 0: passed += 1

    # 19. Reminders List & WhatsApp Link
    total += 1
    ok, r = test_endpoint("Follow-up Reminders (/api/reminders)", "GET", "/api/reminders")
    if ok:
        rems = r.json()
        passed += 1
        if len(rems) > 0 and "whatsapp_link" in rems[0]:
            print(f"       WhatsApp link verified: {rems[0]['whatsapp_link'][:45]}...")

    # 20. Rapid Emergency SOS Triage
    total += 1
    sos_payload = {
        "patient_name": "Cardiac Arrest Emergency",
        "caller_phone": "+91 98888 11111",
        "pickup_address": "Indiranagar Metro Station",
        "emergency_type": "Cardiac / Chest Pain",
        "destination": "Manipal Hospital (Old Airport Road)"
    }
    ok, r = test_endpoint("Rapid Emergency SOS Triage (/api/emergency/sos)", "POST", "/api/emergency/sos", sos_payload, 201)
    if ok: passed += 1

    # 21. CSV Export for Appointments
    total += 1
    ok, r = test_endpoint("Export Appointments CSV (/api/export/appointments.csv)", "GET", "/api/export/appointments.csv")
    if ok and "Token" in r.text: passed += 1

    # 22. CSV Export for Patients
    total += 1
    ok, r = test_endpoint("Export Patients CSV (/api/export/patients.csv)", "GET", "/api/export/patients.csv")
    if ok and "Patient Code" in r.text: passed += 1

    print("=" * 60)
    print(f"TEST RESULTS: {passed} / {total} PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
