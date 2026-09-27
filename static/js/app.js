/* PulseCare Clinic Appointment, Patient & Emergency Management Hub
   Client-side SPA Logic & API Integration
*/

let specialtyChart = null;
let trendChart = null;
let emergencyMap = null;
let mapMarkers = [];
let allDoctors = [];
let allPatients = [];

// Initialize application on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  loadDoctors();
  loadPatientSelectOptions();
  loadDashboard();
  setDefaultDates();

  // Periodic polling for live clinic queue & emergency updates (every 30 seconds)
  setInterval(() => {
    loadLiveQueue();
  }, 30000);
});

// ==========================================
// UTILITY & UI HELPERS
// ==========================================

function initClock() {
  const clockEl = document.getElementById("live-clock");
  function update() {
    const now = new Date();
    if (clockEl) {
      clockEl.innerHTML = `<i class="fa-regular fa-clock mr-1"></i> ${now.toLocaleTimeString()}`;
    }
  }
  update();
  setInterval(update, 1000);
}

function setDefaultDates() {
  const today = new Date().toISOString().split("T")[0];
  const aptDate = document.getElementById("apt-date");
  if (aptDate) aptDate.value = today;

  const remDate = document.getElementById("rem-date");
  if (remDate) {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    remDate.value = nextWeek.toISOString().split("T")[0];
  }
}

function switchTab(tabId) {
  // Hide all sections
  const sections = ["dashboard", "appointments", "patients", "ambulances", "blood", "facilities", "reminders"];
  sections.forEach(sec => {
    const el = document.getElementById(`section-${sec}`);
    if (el) el.classList.add("hidden");

    const btn = document.getElementById(`tab-btn-${sec}`);
    if (btn) {
      btn.classList.remove("active", "bg-sky-600", "text-white", "shadow-md");
      btn.classList.add("text-slate-600");
    }
  });

  // Show active section
  const targetSection = document.getElementById(`section-${tabId}`);
  if (targetSection) targetSection.classList.remove("hidden");

  const targetBtn = document.getElementById(`tab-btn-${tabId}`);
  if (targetBtn) {
    targetBtn.classList.add("active");
    targetBtn.classList.remove("text-slate-600");
  }

  // Lazy load data for the switched tab
  if (tabId === "dashboard") {
    loadDashboard();
  } else if (tabId === "appointments") {
    loadAppointments();
  } else if (tabId === "patients") {
    loadPatients();
  } else if (tabId === "ambulances") {
    loadAmbulances();
    loadAmbulanceRequests();
    setTimeout(initOrRefreshMap, 200);
  } else if (tabId === "blood") {
    loadBloodBanks();
    loadBloodRequests();
    loadDonors();
  } else if (tabId === "facilities") {
    loadFacilities();
  } else if (tabId === "reminders") {
    loadReminders();
  }
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("hidden");
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add("hidden");
}

function dismissAlertBanner() {
  const banner = document.getElementById("active-alert-banner");
  if (banner) banner.classList.add("hidden");
}

// Toast notification helper
function showToast(title, icon = "success") {
  Swal.fire({
    title: title,
    icon: icon,
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true
  });
}

// ==========================================
// INITIAL DATA LOADERS
// ==========================================

async function loadDoctors() {
  try {
    const res = await fetch("/api/doctors");
    allDoctors = await res.json();

    // Populate doctor dropdowns
    const aptDocSelect = document.getElementById("apt-doctor-id");
    const filterDocSelect = document.getElementById("filter-apt-doctor");

    if (aptDocSelect) {
      aptDocSelect.innerHTML = '<option value="">-- Choose Doctor / Specialty --</option>';
      allDoctors.forEach(d => {
        aptDocSelect.innerHTML += `<option value="${d.id}">${d.name} (${d.specialty} - ${d.room_number})</option>`;
      });
    }

    if (filterDocSelect) {
      filterDocSelect.innerHTML = '<option value="all">All Doctors</option>';
      allDoctors.forEach(d => {
        filterDocSelect.innerHTML += `<option value="${d.id}">${d.name}</option>`;
      });
    }
  } catch (err) {
    console.error("Failed to load doctors:", err);
  }
}

async function loadPatientSelectOptions() {
  try {
    const res = await fetch("/api/patients");
    allPatients = await res.json();

    const aptPatSelect = document.getElementById("apt-patient-id");
    const remPatSelect = document.getElementById("rem-patient-id");

    if (aptPatSelect) {
      aptPatSelect.innerHTML = '<option value="">-- Choose Registered Patient --</option>';
      allPatients.forEach(p => {
        aptPatSelect.innerHTML += `<option value="${p.id}">${p.full_name} (${p.patient_code} - ${p.phone})</option>`;
      });
    }

    if (remPatSelect) {
      remPatSelect.innerHTML = '<option value="">-- Choose Patient --</option>';
      allPatients.forEach(p => {
        remPatSelect.innerHTML += `<option value="${p.id}">${p.full_name} (${p.phone})</option>`;
      });
    }
  } catch (err) {
    console.error("Failed to load patient options:", err);
  }
}

// ==========================================
// 1. DASHBOARD & STATS
// ==========================================

async function loadDashboard() {
  try {
    const res = await fetch("/api/dashboard/stats");
    const data = await res.json();

    // Update KPI counters
    document.getElementById("stat-today-total").innerText = data.today_total;
    document.getElementById("stat-completed-today").innerText = `${data.completed_today} completed`;
    document.getElementById("stat-waiting-count").innerText = data.waiting_count;
    document.getElementById("badge-waiting-count").innerText = data.waiting_count;
    document.getElementById("stat-in-consult-count").innerText = data.in_consult_count;
    document.getElementById("stat-available-amb").innerText = data.available_ambulances;
    document.getElementById("stat-total-amb").innerText = data.total_ambulances;
    document.getElementById("badge-amb-active").innerText = data.active_ambulance_requests;
    document.getElementById("stat-urgent-blood").innerText = data.urgent_blood_requests;
    document.getElementById("badge-blood-urgent").innerText = data.urgent_blood_requests;
    document.getElementById("stat-total-patients").innerText = data.total_patients;
    document.getElementById("badge-pending-reminders").innerText = data.pending_reminders;

    // Emergency Banner
    if (data.active_alerts && data.active_alerts.length > 0) {
      const topAlert = data.active_alerts[0];
      const banner = document.getElementById("active-alert-banner");
      const title = document.getElementById("alert-banner-title");
      const msg = document.getElementById("alert-banner-msg");
      if (banner && title && msg) {
        title.innerText = topAlert.title;
        msg.innerText = topAlert.message;
        banner.classList.remove("hidden");
      }
    }

    // Blood stock matrix
    renderDashboardBloodMatrix(data.blood_stock_summary);

    // Specialty Chart
    renderSpecialtyChart(data.specialty_breakdown);

    // Trend Chart
    renderTrendChart(data.trend_data);

    // Load Live Queue widget
    loadLiveQueue();

  } catch (err) {
    console.error("Error loading dashboard stats:", err);
  }
}

function renderDashboardBloodMatrix(summary) {
  const container = document.getElementById("dashboard-blood-matrix");
  if (!container || !summary) return;

  const groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
  container.innerHTML = groups.map(g => {
    const units = summary[g] || 0;
    const isLow = units < 10;
    return `
      <div onclick="switchTab('blood'); searchBloodStock('${g}')" class="cursor-pointer p-2.5 rounded-xl border ${isLow ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200'} text-center hover:scale-105 transition shadow-2xs">
        <span class="text-xs font-bold block ${isLow ? 'text-rose-700' : 'text-slate-700'}">${g}</span>
        <span class="text-lg font-extrabold font-mono ${isLow ? 'text-rose-600 animate-pulse' : 'text-slate-900'}">${units}</span>
        <span class="text-[9px] block text-slate-400">units</span>
      </div>
    `;
  }).join("");
}

function renderSpecialtyChart(breakdown) {
  const ctx = document.getElementById("specialtyChart");
  if (!ctx || !breakdown) return;

  if (specialtyChart) specialtyChart.destroy();

  const labels = breakdown.map(item => item.specialty);
  const counts = breakdown.map(item => item.count);

  specialtyChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: [
          "#0284c7", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"
        ],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 10,
            font: { size: 10 }
          }
        }
      },
      cutout: "68%"
    }
  });
}

function renderTrendChart(trendData) {
  const ctx = document.getElementById("trendChart");
  if (!ctx || !trendData) return;

  if (trendChart) trendChart.destroy();

  const labels = trendData.map(d => {
    const parts = d.date.split("-");
    return `${parts[1]}/${parts[2]}`;
  });
  const values = trendData.map(d => d.count);

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Appointments",
        data: values,
        borderColor: "#0284c7",
        backgroundColor: "rgba(2, 132, 199, 0.08)",
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: "#0284c7",
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { size: 10 } }
        },
        x: {
          ticks: { font: { size: 10 } }
        }
      }
    }
  });
}

async function loadLiveQueue() {
  const container = document.getElementById("dashboard-queue-list");
  if (!container) return;

  try {
    const res = await fetch("/api/queue");
    const data = await res.json();
    const queue = data.queue || [];

    if (queue.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-400">
          <i class="fa-solid fa-mug-hot text-2xl mb-2 text-slate-300"></i>
          <p class="text-xs">No patients currently in queue for today.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = queue.map(item => {
      let statusBadge = "";
      if (item.status === "In-Consultation") {
        statusBadge = `<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span> In Consultation</span>`;
      } else if (item.status === "Waiting") {
        statusBadge = `<span class="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-full">Waiting</span>`;
      } else {
        statusBadge = `<span class="bg-slate-100 text-slate-700 text-[10px] font-semibold px-2 py-0.5 rounded-full">Scheduled</span>`;
      }

      return `
        <div class="p-3 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 flex flex-col items-center justify-center shadow-2xs font-mono font-bold text-sky-600 text-sm">
              ${item.token_number}
            </div>
            <div>
              <h5 class="font-bold text-xs text-slate-900">${item.patient_name} <span class="text-slate-400 font-normal">(${item.age || '--'}y)</span></h5>
              <p class="text-[11px] text-slate-500">${item.doctor_name} &bull; ${item.room_number || 'Room 101'}</p>
            </div>
          </div>
          <div class="text-right">
            ${statusBadge}
            <span class="text-[10px] text-slate-400 block mt-1 font-mono">${item.time_slot.split('-')[0]}</span>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load queue:", err);
  }
}

// ==========================================
// 2. APPOINTMENTS & SCHEDULING
// ==========================================

async function loadAppointments() {
  const tbody = document.getElementById("appointments-table-body");
  if (!tbody) return;

  const dateFilter = document.getElementById("filter-apt-date-select") ? document.getElementById("filter-apt-date-select").value : "today";
  const statusFilter = document.getElementById("filter-apt-status") ? document.getElementById("filter-apt-status").value : "all";
  const docFilter = document.getElementById("filter-apt-doctor") ? document.getElementById("filter-apt-doctor").value : "all";

  let dateParam = "all";
  if (dateFilter === "today") {
    dateParam = new Date().toISOString().split("T")[0];
  } else if (dateFilter === "tomorrow") {
    const tm = new Date();
    tm.setDate(tm.getDate() + 1);
    dateParam = tm.toISOString().split("T")[0];
  }

  let url = `/api/appointments?date=${dateParam}&status=${statusFilter}&doctor_id=${docFilter}`;

  try {
    const res = await fetch(url);
    const appointments = await res.json();

    if (appointments.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-8 text-slate-400">
            <i class="fa-regular fa-calendar-xmark text-2xl mb-1 text-slate-300 block"></i>
            No appointments match the selected criteria.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = appointments.map(apt => {
      // Status formatting
      let statusStyle = "";
      if (apt.status === "Scheduled") statusStyle = "bg-sky-50 text-sky-700 border-sky-200";
      else if (apt.status === "Waiting") statusStyle = "bg-amber-50 text-amber-800 border-amber-200 font-bold";
      else if (apt.status === "In-Consultation") statusStyle = "bg-emerald-50 text-emerald-800 border-emerald-200 font-bold";
      else if (apt.status === "Completed") statusStyle = "bg-slate-100 text-slate-600 border-slate-200";
      else if (apt.status === "Cancelled") statusStyle = "bg-rose-50 text-rose-700 border-rose-200";

      // Contextual status action buttons
      let actionButtons = "";
      if (apt.status === "Scheduled") {
        actionButtons = `
          <button onclick="updateAppointmentStatus(${apt.id}, 'Waiting')" class="bg-amber-500 hover:bg-amber-600 text-white px-2.5 py-1 rounded-lg text-[11px] font-semibold transition" title="Mark Patient Checked In">
            <i class="fa-solid fa-clock mr-1"></i> Check-In
          </button>
        `;
      } else if (apt.status === "Waiting") {
        actionButtons = `
          <button onclick="updateAppointmentStatus(${apt.id}, 'In-Consultation')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded-lg text-[11px] font-semibold transition" title="Call Patient to Doctor Room">
            <i class="fa-solid fa-door-open mr-1"></i> Call In
          </button>
        `;
      } else if (apt.status === "In-Consultation") {
        actionButtons = `
          <button onclick="promptCompleteConsultation(${apt.id}, ${apt.patient_id}, '${apt.doctor_name}', '${apt.doctor_specialty}')" class="bg-sky-600 hover:bg-sky-700 text-white px-2.5 py-1 rounded-lg text-[11px] font-semibold transition" title="Log Clinical Summary & Complete">
            <i class="fa-solid fa-check-double mr-1"></i> Complete Visit
          </button>
        `;
      }

      return `
        <tr class="hover:bg-slate-50/80 transition">
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 font-mono font-bold flex items-center justify-center text-xs">
                ${apt.token_number}
              </span>
              <div>
                <span class="font-mono text-[10px] text-slate-400 block">${apt.appointment_code}</span>
              </div>
            </div>
          </td>
          <td class="px-4 py-3">
            <div class="font-bold text-slate-900 cursor-pointer hover:text-sky-600" onclick="viewPatientProfile(${apt.patient_id})">
              ${apt.patient_name}
            </div>
            <div class="text-[11px] text-slate-500 flex items-center gap-1.5">
              <span>${apt.patient_phone}</span>
              ${apt.blood_group ? `<span class="bg-rose-50 text-rose-700 text-[10px] px-1 rounded font-bold">${apt.blood_group}</span>` : ''}
            </div>
          </td>
          <td class="px-4 py-3">
            <div class="font-semibold text-slate-800">${apt.doctor_name}</div>
            <div class="text-[11px] text-slate-500">${apt.doctor_specialty} &bull; ${apt.room_number}</div>
          </td>
          <td class="px-4 py-3">
            <div class="font-medium text-slate-900">${apt.appointment_date}</div>
            <div class="text-[11px] text-slate-500 font-mono">${apt.time_slot}</div>
          </td>
          <td class="px-4 py-3">
            <span class="bg-slate-100 text-slate-700 text-[11px] px-2 py-0.5 rounded-md font-medium">
              ${apt.visit_type}
            </span>
          </td>
          <td class="px-4 py-3">
            <span class="border px-2.5 py-1 rounded-full text-[11px] inline-block ${statusStyle}">
              ${apt.status}
            </span>
          </td>
          <td class="px-4 py-3 text-right space-x-1">
            ${actionButtons}
            <button onclick="printAppointmentSlip(${apt.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-lg text-[11px] transition" title="Print Token Slip">
              <i class="fa-solid fa-print"></i>
            </button>
            ${apt.status !== 'Cancelled' && apt.status !== 'Completed' ? `
              <button onclick="updateAppointmentStatus(${apt.id}, 'Cancelled')" class="text-rose-500 hover:text-rose-700 p-1 text-xs" title="Cancel Appointment">
                <i class="fa-solid fa-ban"></i>
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load appointments:", err);
  }
}

function filterAppointments() {
  loadAppointments();
}

async function updateAppointmentStatus(aptId, newStatus) {
  try {
    const res = await fetch(`/api/appointments/${aptId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to update status");

    showToast(`Appointment status updated to ${newStatus}`);
    loadAppointments();
    loadDashboard();
  } catch (err) {
    Swal.fire("Update Error", err.message, "error");
  }
}

async function handleBookAppointment(e) {
  e.preventDefault();
  const patientId = document.getElementById("apt-patient-id").value;
  const doctorId = document.getElementById("apt-doctor-id").value;
  const appointmentDate = document.getElementById("apt-date").value;
  const timeSlot = document.getElementById("apt-time-slot").value;
  const visitType = document.getElementById("apt-visit-type").value;
  const reason = document.getElementById("apt-reason").value;
  const notes = document.getElementById("apt-notes").value;

  try {
    const res = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: patientId,
        doctor_id: doctorId,
        appointment_date: appointmentDate,
        time_slot: timeSlot,
        visit_type: visitType,
        reason: reason,
        notes: notes
      })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Booking failed");

    closeModal("book-appointment-modal");
    e.target.reset();

    Swal.fire({
      icon: "success",
      title: "Appointment Confirmed!",
      html: `
        <div class="text-center">
          <p class="text-sm">Assigned Token Number:</p>
          <span class="text-4xl font-extrabold font-mono text-sky-600 my-2 block">${result.appointment.token_number}</span>
          <p class="text-xs text-slate-500">${result.appointment.doctor_name} &bull; ${result.appointment.time_slot}</p>
        </div>
      `,
      confirmButtonText: "Print Slip",
      showCancelButton: true,
      cancelButtonText: "Done"
    }).then(ans => {
      if (ans.isConfirmed) {
        printAppointmentSlip(result.appointment.id);
      }
    });

    loadAppointments();
    loadDashboard();
  } catch (err) {
    Swal.fire("Booking Conflict / Error", err.message, "warning");
  }
}

async function printAppointmentSlip(aptId) {
  try {
    const res = await fetch(`/api/appointments/${aptId}/slip`);
    const slip = await res.json();

    document.getElementById("slip-token").innerText = slip.token_number;
    document.getElementById("slip-code").innerText = slip.appointment_code;
    document.getElementById("slip-patient").innerText = `${slip.patient_name} (${slip.patient_age || '--'}y / ${slip.patient_gender || '--'})`;
    document.getElementById("slip-patient-code").innerText = slip.patient_code;
    document.getElementById("slip-doctor").innerText = slip.doctor_name;
    document.getElementById("slip-specialty").innerText = `${slip.specialty} (${slip.room_number})`;
    document.getElementById("slip-datetime").innerText = `${slip.appointment_date} at ${slip.time_slot}`;
    document.getElementById("slip-visit-type").innerText = slip.visit_type;

    openModal("appointment-slip-modal");
  } catch (err) {
    Swal.fire("Error", "Could not load appointment slip", "error");
  }
}

// ==========================================
// 3. PATIENTS & VISIT HISTORY
// ==========================================

async function loadPatients() {
  const container = document.getElementById("patients-cards-container");
  if (!container) return;

  const search = document.getElementById("patient-search-input") ? document.getElementById("patient-search-input").value.trim() : "";
  const blood = document.getElementById("patient-blood-filter") ? document.getElementById("patient-blood-filter").value : "";

  try {
    const res = await fetch(`/api/patients?search=${encodeURIComponent(search)}&blood_group=${encodeURIComponent(blood)}`);
    const patients = await res.json();

    if (patients.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12 text-slate-400">
          <i class="fa-solid fa-user-slash text-3xl mb-2 text-slate-300"></i>
          <p class="text-sm">No patients found matching your search.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = patients.map(p => {
      return `
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-sky-300 transition flex flex-col justify-between">
          <div>
            <div class="flex items-start justify-between">
              <div>
                <h4 class="font-bold text-slate-900 text-sm hover:text-sky-600 cursor-pointer" onclick="viewPatientProfile(${p.id})">
                  ${p.full_name}
                </h4>
                <span class="text-[10px] font-mono text-slate-400">${p.patient_code}</span>
              </div>
              <span class="px-2 py-0.5 rounded-full text-xs font-bold ${p.blood_group ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-slate-100 text-slate-500'}">
                ${p.blood_group || 'N/A'}
              </span>
            </div>

            <div class="mt-3 space-y-1 text-xs text-slate-600">
              <div class="flex items-center gap-2">
                <i class="fa-solid fa-phone text-slate-400 text-[10px]"></i>
                <span>${p.phone}</span>
              </div>
              <div class="flex items-center gap-2">
                <i class="fa-solid fa-user text-slate-400 text-[10px]"></i>
                <span>${p.age || '--'} yrs &bull; ${p.gender || 'Not specified'}</span>
              </div>
              ${p.emergency_contact_phone ? `
                <div class="flex items-center gap-2 text-amber-700">
                  <i class="fa-solid fa-shield-halved text-amber-500 text-[10px]"></i>
                  <span class="truncate">Emg: ${p.emergency_contact_name || ''} (${p.emergency_contact_phone})</span>
                </div>
              ` : ''}
              ${p.allergies ? `
                <div class="flex items-center gap-2 text-red-600 font-semibold text-[11px]">
                  <i class="fa-solid fa-ban text-[10px]"></i>
                  <span>Allergies: ${p.allergies}</span>
                </div>
              ` : ''}
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span class="text-slate-400 text-[11px]">${p.total_visits} clinical visits</span>
            <button onclick="viewPatientProfile(${p.id})" class="text-sky-600 hover:text-sky-700 font-semibold flex items-center gap-1">
              View History &rarr;
            </button>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load patients:", err);
  }
}

function searchPatients() {
  loadPatients();
}

async function handleRegisterPatient(e) {
  e.preventDefault();
  const payload = {
    full_name: document.getElementById("reg-name").value.trim(),
    phone: document.getElementById("reg-phone").value.trim(),
    age: document.getElementById("reg-age").value,
    gender: document.getElementById("reg-gender").value,
    blood_group: document.getElementById("reg-blood").value,
    email: document.getElementById("reg-email").value.trim(),
    emergency_contact_name: document.getElementById("reg-emg-name").value.trim(),
    emergency_contact_phone: document.getElementById("reg-emg-phone").value.trim(),
    address: document.getElementById("reg-address").value.trim(),
    allergies: document.getElementById("reg-allergies").value.trim(),
    pre_existing_conditions: document.getElementById("reg-conditions").value.trim(),
    notes: document.getElementById("reg-notes").value.trim()
  };

  try {
    const res = await fetch("/api/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Registration failed");

    closeModal("register-patient-modal");
    e.target.reset();

    showToast(`Patient registered: ${result.patient.patient_code}`);
    loadPatients();
    loadPatientSelectOptions();
    loadDashboard();
  } catch (err) {
    Swal.fire("Registration Error", err.message, "error");
  }
}

async function viewPatientProfile(patientId) {
  try {
    const res = await fetch(`/api/patients/${patientId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not fetch patient");

    const p = data.patient;
    document.getElementById("detail-patient-avatar").innerText = p.full_name.substring(0, 2).toUpperCase();
    document.getElementById("detail-patient-name").innerText = p.full_name;
    document.getElementById("detail-patient-code").innerText = p.patient_code;
    document.getElementById("detail-patient-blood").innerText = p.blood_group || "N/A";
    document.getElementById("detail-patient-meta").innerText = `Age: ${p.age || '--'}y &bull; Gender: ${p.gender || '--'} &bull; Phone: ${p.phone}`;
    document.getElementById("detail-patient-emg").innerText = p.emergency_contact_name ? `${p.emergency_contact_name} (${p.emergency_contact_phone})` : "None recorded";
    document.getElementById("detail-patient-allergies").innerText = p.allergies || "None declared";
    document.getElementById("detail-patient-conditions").innerText = p.pre_existing_conditions || "None";
    document.getElementById("detail-patient-address").innerText = p.address || "No address on file";

    // Store current patient id on the Add Visit modal
    document.getElementById("visit-patient-id").value = p.id;

    // Render Visit History
    const visitsContainer = document.getElementById("patient-visits-container");
    if (data.visits && data.visits.length > 0) {
      visitsContainer.innerHTML = data.visits.map(v => {
        return `
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <div class="flex items-center justify-between text-xs mb-1">
              <span class="font-bold text-slate-800">${v.visit_date} &bull; ${v.doctor_name} (${v.department})</span>
              <span class="bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded text-[10px]">${v.visit_type}</span>
            </div>
            <p class="text-xs text-slate-600"><strong>Chief Complaint:</strong> ${v.chief_complaint || 'Routine review'}</p>
            ${v.administrative_notes ? `<p class="text-xs text-slate-500 mt-1 bg-white p-2 rounded border border-slate-100">${v.administrative_notes}</p>` : ''}
            ${v.follow_up_recommended_date ? `<p class="text-[11px] text-amber-700 font-semibold mt-1"><i class="fa-regular fa-clock mr-1"></i> Follow-up recommended: ${v.follow_up_recommended_date}</p>` : ''}
          </div>
        `;
      }).join("");
    } else {
      visitsContainer.innerHTML = `<p class="text-xs text-slate-400 py-3 text-center">No past clinical visit records logged yet.</p>`;
    }

    // Render Past Appointments
    const aptContainer = document.getElementById("patient-appointments-container");
    if (data.appointments && data.appointments.length > 0) {
      aptContainer.innerHTML = data.appointments.map(a => {
        return `
          <div class="p-2.5 rounded-lg border border-slate-200 bg-white flex items-center justify-between text-xs">
            <div>
              <span class="font-bold text-slate-900">${a.appointment_date}</span> &bull; 
              <span class="font-mono text-slate-500">${a.time_slot}</span> &bull; 
              <span>${a.doctor_name}</span>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${a.status === 'Completed' ? 'bg-slate-100 text-slate-600' : 'bg-sky-50 text-sky-700'}">${a.status}</span>
          </div>
        `;
      }).join("");
    } else {
      aptContainer.innerHTML = `<p class="text-xs text-slate-400 py-2">No appointment logs.</p>`;
    }

    openModal("patient-details-modal");
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

function openAddVisitModal() {
  openModal("add-visit-modal");
}

function promptCompleteConsultation(aptId, patientId, doctorName, department) {
  document.getElementById("visit-patient-id").value = patientId;
  document.getElementById("visit-appointment-id").value = aptId;
  document.getElementById("visit-doctor-name").value = doctorName || "Dr. Rajesh Sharma";
  document.getElementById("visit-department").value = department || "General Medicine";
  openModal("add-visit-modal");
}

async function handleAddVisitRecord(e) {
  e.preventDefault();
  const payload = {
    patient_id: document.getElementById("visit-patient-id").value,
    appointment_id: document.getElementById("visit-appointment-id").value || null,
    doctor_name: document.getElementById("visit-doctor-name").value,
    department: document.getElementById("visit-department").value,
    chief_complaint: document.getElementById("visit-complaint").value,
    administrative_notes: document.getElementById("visit-notes").value,
    follow_up_recommended_date: document.getElementById("visit-followup-date").value
  };

  try {
    const res = await fetch("/api/visits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to log visit");

    closeModal("add-visit-modal");
    closeModal("patient-details-modal");
    e.target.reset();

    showToast("Clinical visit recorded successfully");
    loadAppointments();
    loadDashboard();
    loadReminders();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

// ==========================================
// 4. AMBULANCE FLEET & DISPATCH
// ==========================================

function initOrRefreshMap() {
  const mapDiv = document.getElementById("emergency-map");
  if (!mapDiv) return;

  if (!emergencyMap) {
    // Default centered on Bangalore healthcare corridor
    emergencyMap = L.map('emergency-map').setView([12.9716, 77.6412], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(emergencyMap);

    // PulseCare Clinic Primary Marker
    const clinicIcon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="background-color: #0284c7; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><i class="fa-solid fa-hospital text-white text-sm"></i></div>`,
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });
    L.marker([12.9716, 77.6412], { icon: clinicIcon })
      .addTo(emergencyMap)
      .bindPopup("<strong>PulseCare Medical Hub & Clinic</strong><br>24/7 Primary Emergency Base<br>Tel: +91 80 4099 1100");
  } else {
    emergencyMap.invalidateSize();
  }

  // Clear previous markers
  mapMarkers.forEach(m => emergencyMap.removeLayer(m));
  mapMarkers = [];

  // Plot live ambulances on map
  fetch("/api/ambulances")
    .then(r => r.json())
    .then(ambulances => {
      ambulances.forEach(amb => {
        let pinColor = amb.status === "Available" ? "#10b981" : (amb.status === "Dispatched" ? "#ef4444" : "#f59e0b");
        const ambIcon = L.divIcon({
          className: 'custom-marker',
          html: `<div style="background-color: ${pinColor}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2.5px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><i class="fa-solid fa-truck-medical text-white text-xs"></i></div>`,
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        });

        const marker = L.marker([amb.latitude, amb.longitude], { icon: ambIcon })
          .addTo(emergencyMap)
          .bindPopup(`
            <strong>Ambulance: ${amb.vehicle_number}</strong><br>
            Type: ${amb.ambulance_type}<br>
            Driver: ${amb.driver_name} (${amb.driver_phone})<br>
            Status: <strong>${amb.status}</strong><br>
            Location: ${amb.current_location_name}
          `);
        mapMarkers.push(marker);
      });
    });

  // Plot major hospitals
  fetch("/api/facilities?type=Hospital")
    .then(r => r.json())
    .then(facilities => {
      facilities.forEach(fac => {
        const hospIcon = L.divIcon({
          className: 'custom-marker',
          html: `<div style="background-color: #8b5cf6; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 3px 6px rgba(0,0,0,0.25);"><i class="fa-solid fa-square-h text-white text-xs"></i></div>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });
        const marker = L.marker([fac.latitude, fac.longitude], { icon: hospIcon })
          .addTo(emergencyMap)
          .bindPopup(`
            <strong>${fac.name}</strong><br>
            ${fac.facility_type}<br>
            ICU Beds Ready: <strong>${fac.icu_beds_available}</strong><br>
            Helpline: <a href="tel:${fac.emergency_phone}">${fac.emergency_phone}</a>
          `);
        mapMarkers.push(marker);
      });
    });
}

async function loadAmbulances() {
  const container = document.getElementById("ambulance-fleet-container");
  if (!container) return;

  try {
    const res = await fetch("/api/ambulances");
    const fleet = await res.json();

    container.innerHTML = fleet.map(amb => {
      let statusBadge = "";
      if (amb.status === "Available") statusBadge = "bg-emerald-100 text-emerald-800 border-emerald-300";
      else if (amb.status === "Dispatched") statusBadge = "bg-red-100 text-red-700 border-red-300 font-bold animate-pulse";
      else if (amb.status === "On-Route") statusBadge = "bg-amber-100 text-amber-800 border-amber-300";
      else statusBadge = "bg-slate-100 text-slate-600 border-slate-300";

      return `
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="font-mono font-bold text-xs text-slate-900">${amb.vehicle_number}</span>
              <span class="border text-[10px] px-2 py-0.5 rounded-full ${statusBadge}">${amb.status}</span>
            </div>
            <h5 class="font-bold text-xs text-slate-800">${amb.ambulance_type}</h5>
            <p class="text-[11px] text-slate-500 mt-1"><i class="fa-solid fa-location-dot text-slate-400 mr-1"></i> ${amb.current_location_name}</p>
            
            <div class="mt-2.5 p-2 bg-slate-50 rounded-lg text-[11px] space-y-1">
              <div class="flex justify-between">
                <span class="text-slate-400">Driver:</span>
                <span class="font-semibold text-slate-800">${amb.driver_name}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Phone:</span>
                <a href="tel:${amb.driver_phone}" class="text-sky-600 font-semibold">${amb.driver_phone}</a>
              </div>
            </div>

            <div class="mt-2 text-[10px] text-slate-500">
              <strong>Equipped with:</strong> ${amb.equipment || 'Standard first aid'}
            </div>
          </div>

          <div class="mt-3 pt-2.5 border-t border-slate-100 flex gap-2">
            ${amb.status === 'Available' ? `
              <button onclick="quickDispatchAmbulance(${amb.id})" class="flex-1 bg-red-600 hover:bg-red-700 text-white text-[11px] font-bold py-1.5 rounded-lg transition">
                Dispatch Unit
              </button>
            ` : `
              <button onclick="updateAmbulanceStatus(${amb.id}, 'Available')" class="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium py-1.5 rounded-lg transition">
                Set to Available
              </button>
            `}
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load ambulances:", err);
  }
}

async function updateAmbulanceStatus(ambId, newStatus) {
  try {
    const res = await fetch(`/api/ambulances/${ambId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (!res.ok) throw new Error("Failed to update status");
    showToast(`Ambulance set to ${newStatus}`);
    loadAmbulances();
    loadDashboard();
    initOrRefreshMap();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

async function loadAmbulanceRequests() {
  const tbody = document.getElementById("ambulance-requests-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/ambulances/requests");
    const requests = await res.json();

    const countBadge = document.getElementById("ambulance-requests-count");
    if (countBadge) countBadge.innerText = `${requests.length} requests logged`;

    if (requests.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">No active ambulance requests.</td></tr>`;
      return;
    }

    tbody.innerHTML = requests.map(r => {
      let urgencyBadge = "";
      if (r.urgency_level.includes("Critical")) urgencyBadge = "bg-red-50 text-red-700 border-red-200 font-bold";
      else urgencyBadge = "bg-amber-50 text-amber-800 border-amber-200";

      let statusBadge = "";
      if (r.status === "Pending") statusBadge = "bg-amber-100 text-amber-800";
      else if (r.status === "Dispatched") statusBadge = "bg-sky-100 text-sky-800 font-bold";
      else if (r.status === "Transporting") statusBadge = "bg-purple-100 text-purple-800 font-bold";
      else if (r.status === "Completed") statusBadge = "bg-emerald-100 text-emerald-800";
      else statusBadge = "bg-slate-100 text-slate-600";

      return `
        <tr class="hover:bg-slate-50 transition">
          <td class="px-4 py-3">
            <span class="font-mono font-bold text-xs text-slate-900 block">${r.request_code}</span>
            <span class="border text-[10px] px-1.5 py-0.5 rounded-full ${urgencyBadge}">${r.urgency_level.split('/')[0]}</span>
          </td>
          <td class="px-4 py-3">
            <div class="font-bold text-slate-800">${r.caller_name}</div>
            <div class="text-[11px] text-slate-500">${r.caller_phone}</div>
          </td>
          <td class="px-4 py-3 max-w-xs truncate" title="${r.pickup_address}">
            ${r.pickup_address}
          </td>
          <td class="px-4 py-3">
            ${r.destination_facility}
          </td>
          <td class="px-4 py-3">
            ${r.vehicle_number ? `
              <span class="font-mono font-bold text-slate-800 text-[11px] block">${r.vehicle_number}</span>
              <span class="text-[10px] text-slate-500">${r.driver_name || ''}</span>
            ` : '<span class="text-amber-600 text-xs italic">Unassigned</span>'}
          </td>
          <td class="px-4 py-3">
            <span class="px-2 py-0.5 rounded-full text-[11px] ${statusBadge}">${r.status}</span>
          </td>
          <td class="px-4 py-3 text-right space-x-1">
            ${r.status === 'Dispatched' ? `
              <button onclick="updateAmbulanceRequestStatus(${r.id}, 'Transporting')" class="bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded text-[11px] font-semibold">
                Transporting
              </button>
            ` : ''}
            ${r.status === 'Transporting' || r.status === 'Dispatched' ? `
              <button onclick="updateAmbulanceRequestStatus(${r.id}, 'Completed')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2 py-1 rounded text-[11px] font-semibold">
                Complete
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load requests:", err);
  }
}

async function updateAmbulanceRequestStatus(reqId, newStatus) {
  try {
    const res = await fetch(`/api/ambulances/requests/${reqId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (!res.ok) throw new Error("Failed to update request");
    showToast(`Ambulance request set to ${newStatus}`);
    loadAmbulanceRequests();
    loadAmbulances();
    loadDashboard();
    initOrRefreshMap();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

async function handleRequestAmbulance(e) {
  e.preventDefault();
  const payload = {
    caller_name: document.getElementById("amb-caller-name").value.trim(),
    caller_phone: document.getElementById("amb-caller-phone").value.trim(),
    patient_name: document.getElementById("amb-patient-name").value.trim(),
    pickup_address: document.getElementById("amb-pickup-address").value.trim(),
    urgency_level: document.getElementById("amb-urgency").value,
    ambulance_type_needed: document.getElementById("amb-type-needed").value,
    destination_facility: document.getElementById("amb-destination").value,
    notes: document.getElementById("amb-notes").value.trim()
  };

  try {
    const res = await fetch("/api/ambulances/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to dispatch ambulance");

    closeModal("request-ambulance-modal");
    e.target.reset();

    Swal.fire({
      icon: "success",
      title: "Ambulance Dispatched!",
      html: `
        <p class="text-sm">Request Code: <strong>${result.request.request_code}</strong></p>
        <p class="text-xs text-slate-500 mt-1">Vehicle: <strong>${result.request.vehicle_number || 'Next Available'}</strong></p>
        <p class="text-xs text-slate-500">Destination: <strong>${result.request.destination_facility}</strong></p>
      `
    });

    loadAmbulances();
    loadAmbulanceRequests();
    loadDashboard();
    initOrRefreshMap();
  } catch (err) {
    Swal.fire("Dispatch Error", err.message, "error");
  }
}

function quickDispatchAmbulance(ambulanceId) {
  openModal("request-ambulance-modal");
}

// ==========================================
// 5. BLOOD BANK & SOS REQUIREMENTS
// ==========================================

async function loadBloodBanks() {
  const container = document.getElementById("blood-banks-grid");
  if (!container) return;

  try {
    const res = await fetch("/api/blood/banks");
    const banks = await res.json();

    container.innerHTML = banks.map(b => {
      return `
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-start justify-between">
              <div>
                <h5 class="font-bold text-slate-900 text-xs">${b.name}</h5>
                <p class="text-[11px] text-slate-500"><i class="fa-solid fa-location-dot text-slate-400 mr-1"></i> ${b.address}</p>
              </div>
              <span class="bg-sky-50 text-sky-700 text-[10px] font-bold px-2 py-0.5 rounded-md font-mono">${b.distance_km} km</span>
            </div>

            <div class="mt-3 flex items-center justify-between text-xs text-slate-600 bg-slate-50 p-2 rounded-xl">
              <span><i class="fa-regular fa-clock text-slate-400 mr-1"></i> Hours: <strong>${b.operating_hours}</strong></span>
              <a href="tel:${b.contact_phone}" class="text-sky-600 font-bold hover:underline">
                <i class="fa-solid fa-phone mr-1"></i> ${b.contact_phone}
              </a>
            </div>

            <!-- Mini Stock Matrix for this bank -->
            <div class="mt-3 grid grid-cols-4 gap-1.5 text-center text-[10px]">
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">A+</span> <strong>${b.stock_a_pos}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">A-</span> <strong>${b.stock_a_neg}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">B+</span> <strong>${b.stock_b_pos}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">B-</span> <strong>${b.stock_b_neg}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">AB+</span> <strong>${b.stock_ab_pos}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">AB-</span> <strong>${b.stock_ab_neg}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">O+</span> <strong>${b.stock_o_pos}</strong></div>
              <div class="p-1 rounded bg-slate-100 font-mono"><span class="text-slate-400 block text-[9px]">O-</span> <strong>${b.stock_o_neg}</strong></div>
            </div>
          </div>

          <div class="mt-3 pt-2 border-t border-slate-100 flex justify-end">
            <a href="tel:${b.contact_phone}" class="bg-red-50 hover:bg-red-100 text-red-700 text-xs px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1 transition">
              <i class="fa-solid fa-phone"></i> Call Blood Bank
            </a>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load blood banks:", err);
  }
}

async function searchBloodStock(bloodGroup) {
  const container = document.getElementById("blood-banks-grid");
  if (!container) return;

  try {
    const res = await fetch(`/api/blood/search?blood_group=${encodeURIComponent(bloodGroup)}`);
    const data = await res.json();
    const banks = data.banks || [];

    // Highlight button
    document.querySelectorAll(".blood-btn").forEach(b => {
      if (b.innerText.trim() === bloodGroup) {
        b.classList.add("bg-rose-600", "text-white");
        b.classList.remove("bg-white", "text-rose-800");
      } else {
        b.classList.remove("bg-rose-600", "text-white");
        b.classList.add("bg-white", "text-rose-800");
      }
    });

    container.innerHTML = banks.map(b => {
      const units = b.available_units || 0;
      return `
        <div class="bg-white p-4 rounded-2xl border-2 ${units > 0 ? 'border-emerald-300' : 'border-rose-200'} shadow-xs flex flex-col justify-between">
          <div>
            <div class="flex items-start justify-between">
              <div>
                <h5 class="font-bold text-slate-900 text-xs">${b.name}</h5>
                <p class="text-[11px] text-slate-500">${b.address}</p>
              </div>
              <div class="text-center bg-slate-50 px-2 py-1 rounded-lg border border-slate-200">
                <span class="text-[10px] text-slate-400 block">Distance</span>
                <span class="font-mono font-bold text-xs text-slate-800">${b.distance_km} km</span>
              </div>
            </div>

            <!-- Prominent Blood Group Count Display -->
            <div class="my-3 p-3 rounded-xl ${units > 0 ? 'bg-emerald-50 border border-emerald-200' : 'bg-rose-50 border border-rose-200'} flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-8 h-8 rounded-full bg-red-600 text-white font-bold flex items-center justify-center text-xs">
                  ${bloodGroup}
                </span>
                <div>
                  <span class="text-xs font-bold ${units > 0 ? 'text-emerald-800' : 'text-rose-800'}">
                    ${units > 0 ? 'Stock Available' : 'Out of Stock / Critical'}
                  </span>
                  <span class="text-[10px] text-slate-500 block">Regional blood bank stock</span>
                </div>
              </div>
              <span class="text-2xl font-extrabold font-mono ${units > 0 ? 'text-emerald-700' : 'text-rose-600'}">
                ${units} <span class="text-xs font-normal">units</span>
              </span>
            </div>
          </div>

          <div class="flex items-center justify-between pt-2 border-t border-slate-100">
            <span class="text-xs text-slate-500">${b.contact_phone}</span>
            <a href="tel:${b.contact_phone}" class="bg-sky-600 hover:bg-sky-700 text-white text-xs px-3 py-1.5 rounded-lg font-bold flex items-center gap-1 transition">
              <i class="fa-solid fa-phone"></i> Reserve Units
            </a>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed searching blood:", err);
  }
}

async function loadBloodRequests() {
  const container = document.getElementById("blood-sos-demands-container");
  if (!container) return;

  try {
    const res = await fetch("/api/blood/requests");
    const requests = await res.json();

    const activeCount = requests.filter(r => r.status === "Urgent").length;
    const badge = document.getElementById("blood-requests-active-count");
    if (badge) badge.innerText = `${activeCount} urgent requirement(s)`;

    if (requests.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-xs text-slate-400">No active emergency blood requests.</div>`;
      return;
    }

    container.innerHTML = requests.map(r => {
      let isUrgent = r.status === "Urgent";
      return `
        <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${isUrgent ? 'bg-rose-50/40' : 'bg-white'}">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-xl bg-red-600 text-white font-extrabold text-sm flex flex-col items-center justify-center shrink-0">
              ${r.blood_group}
              <span class="text-[8px] font-normal font-sans">${r.units_required}U</span>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h5 class="font-bold text-xs text-slate-900">${r.patient_name}</h5>
                <span class="text-[10px] font-mono text-slate-400">${r.request_code}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isUrgent ? 'bg-red-100 text-red-700 animate-pulse' : 'bg-slate-100 text-slate-600'}">${r.status}</span>
              </div>
              <p class="text-xs text-slate-600 mt-0.5"><strong>Hospital:</strong> ${r.hospital_name} &bull; <strong>Urgency:</strong> ${r.urgency}</p>
              <p class="text-[11px] text-slate-500">Contact: ${r.contact_person} (${r.contact_phone}) &bull; ${r.notes || ''}</p>
            </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <a href="tel:${r.contact_phone}" class="bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition">
              <i class="fa-solid fa-phone text-red-600"></i> Call
            </a>
            ${isUrgent ? `
              <button onclick="updateBloodRequestStatus(${r.id}, 'Fulfilled')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition">
                Mark Fulfilled
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load blood requests:", err);
  }
}

async function updateBloodRequestStatus(reqId, newStatus) {
  try {
    const res = await fetch(`/api/blood/requests/${reqId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    if (!res.ok) throw new Error("Failed to update");
    showToast(`Blood request marked as ${newStatus}`);
    loadBloodRequests();
    loadDashboard();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

async function handleBloodRequest(e) {
  e.preventDefault();
  const payload = {
    patient_name: document.getElementById("bld-patient-name").value.trim(),
    blood_group: document.getElementById("bld-group").value,
    units_required: document.getElementById("bld-units").value,
    hospital_name: document.getElementById("bld-hospital").value.trim(),
    contact_person: document.getElementById("bld-contact-person").value.trim(),
    contact_phone: document.getElementById("bld-contact-phone").value.trim(),
    urgency: document.getElementById("bld-urgency").value,
    notes: document.getElementById("bld-notes").value.trim()
  };

  try {
    const res = await fetch("/api/blood/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to post request");

    closeModal("blood-request-modal");
    e.target.reset();

    showToast("Urgent blood requirement broadcasted!");
    loadBloodRequests();
    loadDashboard();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

async function loadDonors() {
  const container = document.getElementById("blood-donors-grid");
  if (!container) return;

  try {
    const res = await fetch("/api/blood/donors");
    const donors = await res.json();

    container.innerHTML = donors.map(d => {
      return `
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
          <div>
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-xs text-slate-800">${d.full_name}</span>
              <span class="bg-red-100 text-red-700 text-[10px] font-bold px-1.5 rounded">${d.blood_group}</span>
            </div>
            <span class="text-[10px] text-slate-400 block">${d.city}</span>
          </div>
          <a href="tel:${d.phone}" class="w-7 h-7 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs text-sky-600 hover:bg-sky-50 transition" title="Call Donor">
            <i class="fa-solid fa-phone"></i>
          </a>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load donors:", err);
  }
}

async function handleRegisterDonor(e) {
  e.preventDefault();
  const payload = {
    full_name: document.getElementById("donor-name").value.trim(),
    blood_group: document.getElementById("donor-blood").value,
    phone: document.getElementById("donor-phone").value.trim(),
    city: document.getElementById("donor-city").value.trim()
  };

  try {
    const res = await fetch("/api/blood/donors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to register donor");

    closeModal("blood-donor-modal");
    e.target.reset();

    showToast("Voluntary donor registered successfully!");
    loadDonors();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

// ==========================================
// 6. NEARBY HEALTHCARE FACILITIES
// ==========================================

async function loadFacilities() {
  const container = document.getElementById("facilities-grid");
  if (!container) return;

  const typeFilter = document.getElementById("facility-type-filter") ? document.getElementById("facility-type-filter").value : "all";

  try {
    const res = await fetch(`/api/facilities?type=${typeFilter}`);
    const facilities = await res.json();

    container.innerHTML = facilities.map(f => {
      let typeBadge = "";
      if (f.facility_type.includes("Hospital")) typeBadge = "bg-purple-100 text-purple-800";
      else if (f.facility_type.includes("Pharmacy")) typeBadge = "bg-emerald-100 text-emerald-800";
      else typeBadge = "bg-sky-100 text-sky-800";

      return `
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between hover:border-sky-300 transition">
          <div>
            <div class="flex items-start justify-between gap-2">
              <div>
                <h5 class="font-bold text-slate-900 text-sm">${f.name}</h5>
                <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${typeBadge} inline-block mt-1">${f.facility_type}</span>
              </div>
              <span class="text-xs font-mono font-bold bg-slate-100 px-2 py-1 rounded-lg text-slate-700 shrink-0">
                ${f.distance_km} km
              </span>
            </div>

            <p class="text-xs text-slate-500 mt-2"><i class="fa-solid fa-location-dot text-slate-400 mr-1"></i> ${f.address}</p>

            <div class="mt-3 grid grid-cols-2 gap-2 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <div>
                <span class="text-[10px] text-slate-400 block">ICU Beds:</span>
                <span class="font-bold ${f.icu_beds_available > 0 ? 'text-emerald-600' : 'text-slate-500'}">
                  ${f.icu_beds_available > 0 ? `${f.icu_beds_available} Available` : 'None / N/A'}
                </span>
              </div>
              <div>
                <span class="text-[10px] text-slate-400 block">Ambulance:</span>
                <span class="font-semibold text-slate-700">${f.ambulance_service_available ? 'Available 24/7' : 'Standard'}</span>
              </div>
            </div>

            <div class="mt-2 text-[11px] text-slate-500">
              <strong>Specialties:</strong> ${f.specialties || 'Comprehensive Care'}
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] font-semibold text-emerald-700">${f.open_status}</span>
            <a href="tel:${f.emergency_phone}" class="bg-sky-600 hover:bg-sky-700 text-white text-xs px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 shadow-sm transition">
              <i class="fa-solid fa-phone"></i> ${f.emergency_phone}
            </a>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load facilities:", err);
  }
}

// ==========================================
// 7. FOLLOW-UP REMINDERS (WHATSAPP/SMS)
// ==========================================

async function loadReminders() {
  const tbody = document.getElementById("reminders-table-body");
  if (!tbody) return;

  const statusFilter = document.getElementById("reminder-status-filter") ? document.getElementById("reminder-status-filter").value : "all";

  try {
    const res = await fetch(`/api/reminders?status=${statusFilter}`);
    const reminders = await res.json();

    if (reminders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-400">No reminders match the selected filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = reminders.map(r => {
      const isSent = r.status === "Sent";
      return `
        <tr class="hover:bg-slate-50 transition">
          <td class="px-4 py-3">
            <span class="font-bold text-slate-800 text-xs block">${r.patient_name}</span>
            <span class="font-mono text-[10px] text-slate-400">${r.patient_code}</span>
          </td>
          <td class="px-4 py-3 font-mono text-xs text-slate-600">${r.patient_phone}</td>
          <td class="px-4 py-3 font-semibold text-slate-800 text-xs">${r.reminder_date}</td>
          <td class="px-4 py-3 text-xs text-slate-600 max-w-sm truncate" title="${r.reason}">
            ${r.reason}
          </td>
          <td class="px-4 py-3">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isSent ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              ${r.status}
            </span>
          </td>
          <td class="px-4 py-3 text-right">
            <a href="${r.whatsapp_link}" target="_blank" onclick="markReminderSent(${r.id})" class="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-xs transition">
              <i class="fa-brands fa-whatsapp text-sm"></i> Send WhatsApp
            </a>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Failed to load reminders:", err);
  }
}

async function markReminderSent(reminderId) {
  try {
    await fetch(`/api/reminders/${reminderId}/send`, { method: "POST" });
    setTimeout(() => {
      loadReminders();
      loadDashboard();
    }, 1000);
  } catch (err) {
    console.error("Failed to log sent reminder:", err);
  }
}

async function handleCreateReminder(e) {
  e.preventDefault();
  const payload = {
    patient_id: document.getElementById("rem-patient-id").value,
    reminder_date: document.getElementById("rem-date").value,
    reason: document.getElementById("rem-reason").value.trim(),
    channel: document.getElementById("rem-channel").value
  };

  try {
    const res = await fetch("/api/reminders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to create reminder");

    closeModal("create-reminder-modal");
    e.target.reset();

    showToast("Follow-up reminder scheduled!");
    loadReminders();
    loadDashboard();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}

// ==========================================
// 8. RAPID EMERGENCY SOS TRIAGE
// ==========================================

async function handleEmergencySOS(e) {
  e.preventDefault();
  const payload = {
    patient_name: document.getElementById("sos-patient-name").value.trim(),
    caller_phone: document.getElementById("sos-caller-phone").value.trim(),
    pickup_address: document.getElementById("sos-pickup-address").value.trim(),
    emergency_type: document.getElementById("sos-emergency-type").value,
    destination: document.getElementById("sos-destination").value
  };

  try {
    const res = await fetch("/api/emergency/sos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "SOS Triage failed");

    closeModal("emergency-sos-modal");
    e.target.reset();

    Swal.fire({
      icon: "warning",
      title: "🚨 EMERGENCY DISPATCH ACTIVATED!",
      html: `
        <div class="text-left bg-red-50 p-3 rounded-xl border border-red-200 text-xs text-red-900 space-y-1">
          <p><strong>SOS Reference:</strong> ${result.sos_code}</p>
          <p><strong>Assigned Unit:</strong> ${result.ambulance_assigned ? result.ambulance_assigned.vehicle_number : 'Dispatched to Nearest ALS Unit'}</p>
          <p><strong>Driver:</strong> ${result.ambulance_assigned ? result.ambulance_assigned.driver_name + ' (' + result.ambulance_assigned.driver_phone + ')' : 'Contacting station...'}</p>
        </div>
        <p class="text-xs text-slate-500 mt-2">Emergency alerts have been broadcasted across the clinical network.</p>
      `,
      confirmButtonText: "View Live GPS & Dispatch",
      confirmButtonColor: "#dc2626"
    }).then(() => {
      switchTab("ambulances");
    });

    loadDashboard();
  } catch (err) {
    Swal.fire("Error", err.message, "error");
  }
}
