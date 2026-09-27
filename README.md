# PulseCare: Clinic Appointment, Patient & Emergency Management Hub

> **Healthcare Administrative & Emergency Coordination Platform**  
> *Consolidating primary care clinic appointments, patient files, live queue management, ambulance emergency dispatch, and regional blood bank coordination into one accessible digital hub.*

---

## 📌 Scope & Medical Disclaimer

> **Important Administrative Scope Notice:**  
> PulseCare focuses strictly on **administrative, appointment scheduling, ambulance dispatch, and blood bank coordination management**. It does **NOT** provide medical diagnosis, treatment recommendations, clinical prescriptions, or automated medical decision-making.

---

## 🎯 Problem Statement & Solution

Small clinics and primary care practices frequently manage appointments using paper notebooks, WhatsApp messages, phone calls, or disjointed spreadsheets. Simultaneously, patients and their families in emergency situations struggle to find ambulance services, real-time blood group availability, and emergency referral hospitals in their area.

**PulseCare** brings these critical healthcare operations into one unified, responsive platform:
1. **Clinic Operations:** Structured patient registration, appointment scheduling, conflict prevention, real-time queue tokens, and automated follow-up reminders via WhatsApp.
2. **Emergency Coordination:** Rapid SOS triage, ambulance fleet dispatch with interactive GPS tracking, regional blood stock searching across blood banks, urgent blood requirement broadcasting, and nearby hospital directories.

---

## 🚀 Key Features Implemented

| Category | Feature | Description |
|---|---|---|
| 👤 **Patients** | **Patient Registration** | Register patients with demographic info, blood group, emergency contacts, known allergies, and pre-existing conditions. Auto-generates unique ID (e.g. `PT-2026-001`). |
| 🔎 **Patients** | **Live Patient Search** | Real-time search across patient name, phone number, patient code, and blood group. |
| 🗂️ **Visits** | **Visit History & Records** | Chronological record of past consultations, chief complaints, administrative notes, and recommended follow-up dates. |
| 📅 **Appointments** | **Smart Booking & Scheduling** | Schedule appointments by doctor and specialty with conflict-checking that prevents double-booking time slots. |
| 📋 **Appointments** | **Status Management** | State progression (`Scheduled` ➔ `Waiting` ➔ `In-Consultation` ➔ `Completed` / `Cancelled`) with timestamp logging. |
| 🔢 **Appointments** | **Live Token Queue Board** | Real-time clinic token waiting display (`T-01`, `T-02`, etc.) for waiting room reception screens. |
| 🖨️ **Appointments** | **Printable Appointment Slip** | Printable receipt and slip modal with clinic header, doctor details, token number, and barcode format. |
| 🔔 **Reminders** | **Follow-up Reminders** | Track patients due for review; 1-click WhatsApp messaging button generating pre-populated `https://wa.me/?text=...` links. |
| 📊 **Dashboard** | **Analytics & KPI Counters** | Key metrics, specialty breakdown doughnut chart, 7-day patient load trend, and regional blood stock indicators. |
| 🚑 **Ambulances** | **Ambulance SOS Dispatch** | Submit urgent pickup requests (Critical, High, Moderate), auto-assign the nearest vehicle, and track dispatch status. |
| 📍 **Ambulances** | **Live GPS Fleet Map** | Interactive Leaflet map displaying real-time positions and availability of BLS/ALS ambulances and clinic bases. |
| 🩸 **Blood Bank** | **Blood Group Search** | Search stock levels across 8 blood types (A+, A-, B+, B-, AB+, AB-, O+, O-) across regional blood banks. |
| 🚨 **Blood Bank** | **Urgent Blood SOS Demands** | Post and broadcast emergency blood requirements to regional centers and voluntary donors. |
| 🤝 **Blood Donors** | **Voluntary Donor Network** | Directory of voluntary blood donors ready for replacement donations. |
| 🏥 **Facilities** | **Nearby Healthcare Directory** | Directory of referral hospitals, trauma centers, ICU bed availability, and 24/7 pharmacies with 1-click calling. |
| 🚨 **Triage** | **Rapid Emergency SOS** | High-priority panic triage modal that dispatches ambulances and alerts network staff in seconds. |
| 📁 **Compliance** | **Data Export to CSV** | 1-click export of clinic appointments and patient directory to CSV format for records. |

---

## 🛠️ Architecture & Technology Stack

- **Backend:** Python 3.12, Flask 3.1 (RESTful API architecture & server-side routing)
- **Database:** SQLite with thread-safe connections, automatic schema migration, and comprehensive seed data
- **Production Server:** Gunicorn WSGI server with multi-threaded workers
- **Frontend:** Responsive SPA using Tailwind CSS, FontAwesome 6, Chart.js (analytics), Leaflet 1.9.4 (GPS mapping), and SweetAlert2
- **Containerization:** Production Docker container optimized for Google Cloud Run (zero-dependency build, non-root execution, `$PORT` environment variable support)

---

## 🏃 Local Quickstart

### Prerequisites
- Python 3.10+ installed

### Steps:
1. Navigate to the project directory:
   ```bash
   cd clinic-emergency-system
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Running Automated Test Suite:
Run the comprehensive 22-step verification suite:
```bash
python test_suite.py
```
*(All 22/22 tests verify health endpoints, patient CRUD, appointment conflict detection, status progression, ambulance dispatch, and blood search).*

---

## ☁️ Deploying to Google Cloud Run

Google Cloud Run allows deploying the containerized application as a managed, auto-scaling service.

### Option A: 1-Click Deployment via `gcloud` CLI (Recommended)

1. Make sure you have the [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. Run the deployment command from the project root:
   ```bash
   gcloud run deploy pulsecare \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080
   ```
   *(Or on Windows, simply double-click `deploy.bat` or run `./deploy.sh` on Linux/macOS).*

3. `gcloud` will automatically build the container via Cloud Build and output your live service URL:
   ```
   Service [pulsecare] revision [pulsecare-00001-abc] has been deployed and is serving 100 percent of traffic.
   Service URL: https://pulsecare-xxxxxxx-uc.a.run.app
   ```

---

### Option B: Deploying via Google Cloud Console (Web GUI)

1. Go to the [Google Cloud Run Console](https://console.cloud.google.com/run).
2. Click **Create Service**.
3. Select **"Continuously deploy from a repository"** or **"Deploy one revision from an existing container image"**.
   - If using source: Connect your GitHub/Git repository or Cloud Source Repository containing this folder.
   - Choose **Dockerfile** as the build configuration.
4. Set Service Settings:
   - **Service name:** `pulsecare-clinic`
   - **Region:** `us-central1` (or your preferred region)
   - **Authentication:** Check **"Allow unauthenticated invocations"** (so the jury can access the application).
   - **Container Port:** `8080` (Default).
5. Click **Create**. Within 2 minutes, Google Cloud Run will provide your public URL!

---

## 🧪 Verification & Health Check

Google Cloud Run monitors container liveness using the `/health` endpoint:
- **Health Check URL:** `https://<YOUR-CLOUD-RUN-URL>/health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "PulseCare Clinic & Emergency Management System",
    "timestamp": "2026-09-27T15:20:00.000000",
    "disclaimer": "Administrative, appointment & emergency coordination portal. No medical diagnosis or treatment."
  }
  ```

---

## 📋 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check for Cloud Run container monitoring |
| `/api/dashboard/stats` | GET | Aggregated clinic metrics, specialty distribution, weekly trend, blood totals |
| `/api/patients` | GET, POST | Search patients by query/blood group; register new patient |
| `/api/patients/<id>` | GET, PUT | View full patient profile with visit history; update details |
| `/api/appointments` | GET, POST | Filter appointments; schedule new appointment with conflict check |
| `/api/appointments/<id>/status` | PUT | Transition status (`Scheduled`, `Waiting`, `In-Consultation`, `Completed`, `Cancelled`) |
| `/api/queue` | GET | Current day live token waiting queue |
| `/api/appointments/<id>/slip` | GET | Printable appointment token slip data |
| `/api/visits` | POST | Log clinical visit summary & trigger auto-reminder |
| `/api/reminders` | GET, POST | Retrieve upcoming follow-ups; schedule manual reminders |
| `/api/reminders/<id>/send` | POST | Mark reminder as dispatched and log WhatsApp trigger |
| `/api/ambulances` | GET | Real-time ambulance fleet with GPS coordinates and equipment |
| `/api/ambulances/request` | POST | Submit emergency ambulance request and assign vehicle |
| `/api/ambulances/requests` | GET | List active ambulance runs |
| `/api/ambulances/requests/<id>/status` | PUT | Update trip status (`Dispatched`, `Transporting`, `Completed`) |
| `/api/blood/banks` | GET | Directory of regional blood banks and unit counts |
| `/api/blood/search` | GET | Search blood availability by group (e.g. `O-`) |
| `/api/blood/request` | POST | Post emergency blood requirement SOS |
| `/api/blood/donors` | GET, POST | List and register voluntary donors |
| `/api/facilities` | GET | Directory of nearby hospitals, trauma centers, and pharmacies |
| `/api/emergency/sos` | POST | Unified rapid emergency triage and immediate ambulance dispatch |
| `/api/export/appointments.csv` | GET | Download appointments CSV report |
| `/api/export/patients.csv` | GET | Download patient directory CSV report |
