/**
 * SAKEC TBI Platform — Render + OneDrive + Account Management Controller
 * Developed by Dr. Rohan Appasaheb Borgalli
 */

let CURRENT_USER = null;
let AUTH_TOKEN = localStorage.getItem("sakec_token") || null;
let SETTINGS = {};
let ALL_STARTUPS = [];
let STARTUPS = [];
let CURRENT_STARTUP_ID = 1;
let YEAR_FILTER = "all";
let TYPE_FILTER = "all";
let LATEST_SIMULATION_RESULT = null;

document.addEventListener("DOMContentLoaded", async () => {
  await loadPublicOverview();
  const ok = await checkAuth();
  if (ok) await enterWorkspace();
});

async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (AUTH_TOKEN) headers["Authorization"] = `Bearer ${AUTH_TOKEN}`;
  const config = { method, headers };
  if (body) config.body = JSON.stringify(body);
  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401 && endpoint !== "/api/login" && !endpoint.startsWith("/api/public")) {
      showLoginGate();
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error("API Error:", endpoint, err);
    return null;
  }
}

async function loadPublicOverview() {
  const res = await apiCall("/api/public/overview");
  if (!res) return;
  document.getElementById("pubTotal").textContent = res.total;
  document.getElementById("pubPvt").textContent = res.pvt_ltd;
  document.getElementById("pubPre").textContent = res.pre_incubation;
  document.getElementById("publicShowcaseList").innerHTML = (res.startups || []).map(s => `
    <div style="background:#f8fafc;border:1px solid var(--border);border-radius:6px;padding:0.65rem 0.85rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;">
        <b style="color:var(--primary);font-size:0.9rem;">${s.name}</b>
        <span class="badge ${s.incubation_type === "Incubated (Pvt. Ltd.)" ? "badge-green" : "badge-purple"}">${s.incubation_type}</span>
      </div>
      <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.2rem;">${s.tagline}</div>
      <div style="font-size:0.74rem;color:var(--primary-light);margin-top:0.2rem;">Years: ${s.active_years}${s.cin ? " &bull; CIN: " + s.cin : ""}</div>
    </div>
  `).join("");
}

async function checkAuth() {
  if (!AUTH_TOKEN) { showLoginGate(); return false; }
  const res = await apiCall("/api/me");
  if (res && res.user) {
    CURRENT_USER = res.user;
    if (CURRENT_USER.role === "founder" && CURRENT_USER.startup_id) CURRENT_STARTUP_ID = CURRENT_USER.startup_id;
    return true;
  }
  showLoginGate();
  return false;
}

function showLoginGate() {
  CURRENT_USER = null;
  document.getElementById("loginGateView").style.display = "block";
  document.getElementById("appWorkspace").style.display = "none";
  document.getElementById("headerUserStatus").style.display = "none";
}

async function enterWorkspace() {
  document.getElementById("loginGateView").style.display = "none";
  document.getElementById("appWorkspace").style.display = "flex";
  document.getElementById("headerUserStatus").style.display = "flex";
  document.getElementById("currentUserDisplay").textContent = `${CURRENT_USER.full_name} (${CURRENT_USER.role.replace("_", " ")})`;
  document.getElementById("adminNavTab").style.display = CURRENT_USER.role === "faculty_incharge" ? "inline-flex" : "none";

  await loadSettings();
  await loadAllStartupsForDropdowns();
  await refreshActiveView();
}

async function handleLogin(e) {
  e.preventDefault();
  const res = await apiCall("/api/login", "POST", {
    username: document.getElementById("loginUsername").value,
    password: document.getElementById("loginPassword").value
  });
  if (res && res.token) {
    AUTH_TOKEN = res.token;
    localStorage.setItem("sakec_token", AUTH_TOKEN);
    CURRENT_USER = res.user;
    if (CURRENT_USER.role === "founder" && CURRENT_USER.startup_id) CURRENT_STARTUP_ID = CURRENT_USER.startup_id;
    await enterWorkspace();
  } else {
    alert(res?.error || "Invalid username or password.");
  }
}

function logout() {
  apiCall("/api/logout", "POST");
  AUTH_TOKEN = null;
  localStorage.removeItem("sakec_token");
  showLoginGate();
}

function closeModal(id) { document.getElementById(id).classList.remove("active"); }
function openChangePwdModal() { document.getElementById("changePwdModal").classList.add("active"); }
async function handleChangePassword(e) {
  e.preventDefault();
  const res = await apiCall("/api/change-password", "POST", {
    old_password: document.getElementById("cpOld").value,
    new_password: document.getElementById("cpNew").value
  });
  if (res && res.status === "password_changed") {
    alert("Password updated successfully.");
    closeModal("changePwdModal");
  } else {
    alert(res?.error || "Failed to change password.");
  }
}

async function loadSettings() {
  const res = await apiCall("/api/settings");
  if (!res || !res.settings) return;
  SETTINGS = res.settings;
  const odUrl = SETTINGS.onedrive_master_upload_url || "https://onedrive.live.com/";
  const odAcc = SETTINGS.onedrive_account || "incubation@sakec.ac.in";
  document.getElementById("odAccountLabel").textContent = odAcc;
  document.getElementById("odMasterUploadBtn").href = odUrl;
  const sEmail = document.getElementById("setOdEmail");
  const sUrl = document.getElementById("setOdUrl");
  if (sEmail) sEmail.value = odAcc;
  if (sUrl) sUrl.value = odUrl;
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const res = await apiCall("/api/settings", "POST", {
    onedrive_account: document.getElementById("setOdEmail").value,
    onedrive_master_upload_url: document.getElementById("setOdUrl").value
  });
  if (res && res.status === "settings_saved") {
    alert("OneDrive repository settings saved!");
    await loadSettings();
  }
}

function setYearFilter(year) {
  YEAR_FILTER = year;
  document.querySelectorAll(".year-pill").forEach(b => b.classList.toggle("active", b.dataset.year === year));
  refreshActiveView();
}

function setTypeFilter(type) {
  TYPE_FILTER = type;
  document.querySelectorAll(".type-pill").forEach(b => b.classList.toggle("active", b.dataset.type === type));
  refreshActiveView();
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach(b => b.classList.toggle("active", b.getAttribute("onclick").includes(tabId)));
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");
  refreshActiveView();
}

function openOfficialYearReport() {
  window.open(`/api/export/detailed-report?year=${encodeURIComponent(YEAR_FILTER)}&token=${encodeURIComponent(AUTH_TOKEN)}`, "_blank");
}
function exportPortfolioCSV() {
  window.open(`/api/export/csv?year=${encodeURIComponent(YEAR_FILTER)}&token=${encodeURIComponent(AUTH_TOKEN)}`, "_blank");
}
function exportInternsCSV() {
  window.open(`/api/export/interns-csv?year=${encodeURIComponent(YEAR_FILTER)}&token=${encodeURIComponent(AUTH_TOKEN)}`, "_blank");
}
function downloadJsonBackup() {
  window.open(`/api/admin/backup-json?token=${encodeURIComponent(AUTH_TOKEN)}`, "_blank");
}

async function loadAllStartupsForDropdowns() {
  const res = await apiCall("/api/startups");
  if (!res || !res.startups) return;
  ALL_STARTUPS = res.startups;

  const populate = (id, includeAll = false, blankLabel = null) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const prev = sel.value;
    sel.innerHTML = includeAll ? `<option value="all">${blankLabel || "All Startups"}</option>` : (blankLabel ? `<option value="">${blankLabel}</option>` : "");
    ALL_STARTUPS.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} [${s.incubation_type === "Incubated (Pvt. Ltd.)" ? "Pvt. Ltd." : "Pre-Incubation"}]`;
      sel.appendChild(opt);
    });
    if (prev && [...sel.options].some(o => o.value === prev)) sel.value = prev;
    else if (!includeAll && !blankLabel && CURRENT_STARTUP_ID) sel.value = CURRENT_STARTUP_ID;
  };

  populate("dtStartupSelect");
  populate("usimStartupSelect");
  populate("milestoneStartupSelect");
  populate("mentorStartupSelect");
  populate("addInternStartup");
  populate("addDocStartup");
  populate("cuStartup", false, "-- None (Admin/Authority/Mentor) --");
  populate("internStartupFilter", true);
  populate("docStartupFilter", true);
}

async function refreshActiveView() {
  await loadPortfolioData();
  const activeTab = document.querySelector(".tab-content.active")?.id;
  if (activeTab === "tab-documents") await loadDocumentsTable();
  if (activeTab === "tab-digital-twin") await loadDigitalTwin(CURRENT_STARTUP_ID);
  if (activeTab === "tab-interns") await loadInternsTable();
  if (activeTab === "tab-usim") await prefillSimulator(CURRENT_STARTUP_ID);
  if (activeTab === "tab-milestones") await loadMilestones(CURRENT_STARTUP_ID);
  if (activeTab === "tab-mentorship") await loadMentorshipReviews();
  if (activeTab === "tab-scale") await loadUsersTable();
}

async function loadPortfolioData() {
  const qs = `?year=${encodeURIComponent(YEAR_FILTER)}&type=${encodeURIComponent(TYPE_FILTER)}`;
  const [stRes, anRes] = await Promise.all([
    apiCall(`/api/startups${qs}`),
    apiCall(`/api/analytics/portfolio?year=${encodeURIComponent(YEAR_FILTER)}`)
  ]);
  if (stRes && stRes.startups) {
    STARTUPS = stRes.startups;
    renderPortfolioTable();
  }
  if (anRes && anRes.summary) {
    const sum = anRes.summary;
    document.getElementById("kpiTotalStartups").textContent = sum.total_startups;
    document.getElementById("kpiPvtLtd").textContent = sum.pvt_ltd_count;
    document.getElementById("kpiPreInc").textContent = sum.pre_incubation_count;
    document.getElementById("kpiTotalStudents").textContent = sum.total_students_engaged;
    document.getElementById("kpiDocsProgress").textContent = `${sum.docs_submitted}/${sum.docs_total}`;
    document.getElementById("kpiYearLabel").textContent = YEAR_FILTER === "all" ? "Across 2024-25, 2025-26 & 2026-27" : `Academic Year ${YEAR_FILTER}`;
    renderYearSummaryCards(sum.year_summary || {});
  }
}

function renderYearSummaryCards(yearSummary) {
  const container = document.getElementById("yearSummaryCards");
  if (!container) return;
  container.innerHTML = "";
  ["2024-25", "2025-26", "2026-27"].forEach(yr => {
    const info = yearSummary[yr] || { total: 0, pvt_ltd: 0, pre_incubation: 0, students_engaged: 0 };
    const card = document.createElement("div");
    card.className = "year-summary-card";
    if (YEAR_FILTER === yr) card.style.borderLeftColor = "var(--accent)";
    card.onclick = () => setYearFilter(yr);
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <h4>📅 Academic Year ${yr}</h4>
        <button class="btn btn-outline btn-sm" onclick="event.stopPropagation();window.open('/api/export/detailed-report?year=${yr}&token=${encodeURIComponent(AUTH_TOKEN)}','_blank')">🖨️ PDF</button>
      </div>
      <div class="year-summary-stats" style="margin-top:0.35rem;">
        <span><b>${info.total}</b> Ventures</span>
        <span class="badge badge-green">${info.pvt_ltd} Pvt. Ltd.</span>
        <span class="badge badge-purple">${info.pre_incubation} Pre-Inc.</span>
        <span><b>${info.students_engaged}</b> Students</span>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderPortfolioTable() {
  const pvtBody = document.getElementById("pvtPortfolioTableBody");
  const preBody = document.getElementById("prePortfolioTableBody");
  if (!pvtBody || !preBody) return;

  const pvtList = STARTUPS.filter(s => s.incubation_type === "Incubated (Pvt. Ltd.)");
  const preList = STARTUPS.filter(s => s.incubation_type !== "Incubated (Pvt. Ltd.)");

  pvtBody.innerHTML = pvtList.map(s => {
    const dirsText = (s.directors || []).length
      ? s.directors.map(d => `<div style="font-size:0.76rem;"><b>${d.name}</b> <span style="color:var(--primary);font-family:monospace;">(DIN: ${d.din})</span></div>`).join("")
      : `<span>${s.founder_name}</span>`;
    const canEdit = CURRENT_USER.role === "faculty_incharge" || (CURRENT_USER.role === "founder" && CURRENT_USER.startup_id === s.id);
    return `
      <tr>
        <td><b>${s.name}</b>${s.former_names ? `<div style="font-size:0.73rem;color:var(--text-muted);">Formerly: ${s.former_names}</div>` : ""}<div style="font-size:0.73rem;color:var(--text-muted);">${s.stage}</div></td>
        <td><div style="font-family:monospace;font-weight:700;color:var(--primary);font-size:0.8rem;">${s.cin || "Pending"}</div><div style="font-size:0.73rem;color:var(--text-muted);">Inc: ${s.incorporation_date || "-"} | ${s.roc || ""}</div></td>
        <td><span class="badge badge-gray">${s.active_years}</span></td>
        <td>${dirsText}</td>
        <td><button class="btn btn-outline btn-sm" onclick="viewStartupInterns(${s.id})">🎓 ${s.intern_count || 0}</button></td>
        <td><button class="btn btn-outline btn-sm" onclick="viewStartupDocs(${s.id})">☁️ ${s.docs_submitted || 0}/${s.docs_total || 0}</button></td>
        <td><span class="badge badge-blue">Phase ${s.current_phase}</span></td>
        <td>
          <div style="display:flex;gap:0.35rem;">
            <button class="btn btn-outline btn-sm" onclick="viewStartupDetail(${s.id})">360°</button>
            ${canEdit ? `<button class="btn btn-primary btn-sm" onclick="openEditStartupProfileModal(${s.id})">✏️ Edit</button>` : ""}
          </div>
        </td>
      </tr>
    `;
  }).join("") || `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:1.2rem;">No Incubated (Pvt. Ltd.) startups in this filter.</td></tr>`;

  preBody.innerHTML = preList.map(s => {
    const canEdit = CURRENT_USER.role === "faculty_incharge" || (CURRENT_USER.role === "founder" && CURRENT_USER.startup_id === s.id);
    return `
      <tr>
        <td><b>${s.name}</b>${s.former_names ? `<div style="font-size:0.73rem;color:var(--text-muted);">Formerly: ${s.former_names}</div>` : ""}<div style="font-size:0.74rem;color:var(--text-muted);">${s.tagline}</div></td>
        <td>${s.department}</td>
        <td><span class="badge badge-gray">${s.active_years}</span></td>
        <td><b>${s.founder_name}</b><div style="font-size:0.73rem;color:var(--text-muted);">${s.founder_email || ""}</div></td>
        <td><button class="btn btn-outline btn-sm" onclick="viewStartupInterns(${s.id})">🎓 ${s.intern_count || 0}</button></td>
        <td><button class="btn btn-outline btn-sm" onclick="viewStartupDocs(${s.id})">☁️ ${s.docs_submitted || 0}/${s.docs_total || 0}</button></td>
        <td><span class="badge badge-purple">Phase ${s.current_phase}</span></td>
        <td>
          <div style="display:flex;gap:0.35rem;">
            <button class="btn btn-outline btn-sm" onclick="viewStartupDetail(${s.id})">360°</button>
            ${canEdit ? `<button class="btn btn-primary btn-sm" onclick="openEditStartupProfileModal(${s.id})">✏️ Edit</button>` : ""}
          </div>
        </td>
      </tr>
    `;
  }).join("") || `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:1.2rem;">No Pre-Incubation ventures in this filter.</td></tr>`;
}

function filterPortfolioTable() {
  const q = document.getElementById("portfolioSearchInput").value.toLowerCase();
  document.querySelectorAll("#pvtPortfolioTableBody tr, #prePortfolioTableBody tr").forEach(r => r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none");
}

function viewStartupDetail(id) { CURRENT_STARTUP_ID = id; document.getElementById("dtStartupSelect").value = id; switchTab("tab-digital-twin"); }
function viewStartupInterns(id) { document.getElementById("internStartupFilter").value = String(id); switchTab("tab-interns"); }
function viewStartupDocs(id) { document.getElementById("docStartupFilter").value = String(id); switchTab("tab-documents"); }

// DOCUMENTS & ONEDRIVE HUB
async function loadDocumentsTable() {
  const stId = document.getElementById("docStartupFilter")?.value || "all";
  const res = await apiCall(`/api/documents?year=${encodeURIComponent(YEAR_FILTER)}&startup_id=${encodeURIComponent(stId)}`);
  const tbody = document.getElementById("documentsTableBody");
  if (!tbody) return;
  const masterOd = SETTINGS.onedrive_master_upload_url || "https://onedrive.live.com/";

  tbody.innerHTML = (res?.documents || []).map(d => {
    const bClass = d.status === "Verified" ? "badge-green" : (d.status === "Submitted" ? "badge-blue" : (d.status === "Revision Needed" ? "badge-red" : "badge-gold"));
    const uploadLink = d.onedrive_folder_url || masterOd;
    const fileCell = d.onedrive_url
      ? `<a href="${d.onedrive_url}" target="_blank" style="color:var(--info);font-weight:600;">🔗 Open File</a>`
      : `<a href="${uploadLink}" target="_blank" style="color:var(--text-muted);font-size:0.78rem;">☁️ Upload to OneDrive</a>`;

    let actions = `<button class="btn btn-outline btn-sm" onclick="submitDocLink(${d.id})">📎 Submit Link</button>`;
    if (CURRENT_USER.role === "faculty_incharge" || CURRENT_USER.role === "mentor") {
      actions += ` <button class="btn btn-accent btn-sm" onclick="verifyDoc(${d.id},'Verified')">✓ Verify</button>`;
    }
    return `
      <tr>
        <td><b>${d.startup_name}</b></td>
        <td><b>${d.doc_type}</b><div style="font-size:0.74rem;color:var(--text-muted);">${d.title}</div></td>
        <td><span class="badge badge-gray">${d.academic_year}</span></td>
        <td><span class="badge ${bClass}">${d.status}</span></td>
        <td>${fileCell}</td>
        <td><div style="font-size:0.78rem;">${d.uploaded_by || "-"}</div><div style="font-size:0.73rem;color:var(--text-muted);">${d.admin_remarks || ""}</div></td>
        <td style="white-space:nowrap;">${actions}</td>
      </tr>
    `;
  }).join("") || `<tr><td colspan="7" style="text-align:center;padding:1.5rem;color:var(--text-muted);">No document records found.</td></tr>`;
}

async function submitDocLink(docId) {
  const url = prompt("Paste the uploaded OneDrive file link (from incubation@sakec.ac.in OneDrive):");
  if (!url) return;
  const res = await apiCall(`/api/documents/${docId}`, "PUT", { onedrive_url: url.trim(), status: "Submitted", admin_remarks: "Uploaded to incubation@sakec.ac.in OneDrive" });
  if (res && res.status === "document_updated") { await loadDocumentsTable(); await loadPortfolioData(); }
}

async function verifyDoc(docId, status) {
  const remarks = prompt("Admin verification remarks:", "Verified on incubation@sakec.ac.in OneDrive by Dr. Rohan Borgalli");
  if (remarks === null) return;
  const res = await apiCall(`/api/documents/${docId}`, "PUT", { status, admin_remarks: remarks });
  if (res && res.status === "document_updated") { await loadDocumentsTable(); await loadPortfolioData(); }
}

function openAddDocModal() {
  if (CURRENT_USER.role === "founder" && CURRENT_USER.startup_id) document.getElementById("addDocStartup").value = CURRENT_USER.startup_id;
  document.getElementById("addDocModal").classList.add("active");
}
async function handleAddDocument(e) {
  e.preventDefault();
  const res = await apiCall("/api/documents", "POST", {
    startup_id: parseInt(document.getElementById("addDocStartup").value),
    academic_year: document.getElementById("addDocYear").value,
    doc_type: document.getElementById("addDocType").value,
    title: document.getElementById("addDocTitle").value,
    onedrive_url: document.getElementById("addDocUrl").value
  });
  if (res && res.status === "document_added") {
    closeModal("addDocModal");
    await loadDocumentsTable();
    await loadPortfolioData();
  } else {
    alert(res?.error || "Failed to add document.");
  }
}

// WORKOS DIGITAL TWIN
async function loadDigitalTwin(startupId) {
  CURRENT_STARTUP_ID = parseInt(startupId);
  const [sRes, dtRes] = await Promise.all([apiCall(`/api/startups/${startupId}`), apiCall(`/api/startups/${startupId}/digital-twin`)]);
  if (!sRes || !sRes.startup) return;
  const s = sRes.startup, dt = (dtRes && dtRes.digital_twin) || {};
  const isPvt = s.incubation_type === "Incubated (Pvt. Ltd.)";
  const odUrl = s.onedrive_folder_url || SETTINGS.onedrive_master_upload_url || "https://onedrive.live.com/";

  document.getElementById("digitalTwinHeader").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
      <div>
        <h2 style="color:var(--primary);font-size:1.3rem;">${s.name}</h2>
        <div style="color:var(--text-muted);font-size:0.86rem;">${s.tagline}</div>
        <div style="margin-top:0.45rem;display:flex;gap:0.4rem;flex-wrap:wrap;">
          <span class="badge ${isPvt ? "badge-green" : "badge-purple"}">${s.incubation_type}</span>
          <span class="badge badge-gray">Years: ${s.active_years}</span>
          <span class="badge badge-blue">Phase ${s.current_phase}</span>
          <span class="badge badge-gold">Health: ${s.health_score}/100</span>
        </div>
      </div>
      <div style="text-align:right;font-size:0.84rem;">
        <b>Founder(s):</b> ${s.founder_name}<br>
        <b>Contact:</b> ${s.founder_email}${s.founder_phone ? " | " + s.founder_phone : ""}<br>
        <a href="${odUrl}" target="_blank" style="color:var(--info);font-weight:600;">☁️ OneDrive Folder</a>
        ${s.website_url ? ` &bull; <a href="${s.website_url}" target="_blank" style="color:var(--info);font-weight:600;">🔗 Website / MCA</a>` : ""}
      </div>
    </div>
  `;

  const mcaCard = document.getElementById("mcaCorporateCard");
  if (isPvt) {
    const dirsRows = (s.directors || []).map(d => `<tr><td><b>${d.name}</b></td><td style="font-family:monospace;font-weight:700;">${d.din}</td><td>${d.designation || "Director"}</td><td>${d.appointment_date || "-"}</td></tr>`).join("");
    mcaCard.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;"><h3 style="color:var(--primary);font-size:0.98rem;">🏛️ MCA Corporate Registry (Pvt. Ltd.)</h3><span class="badge badge-green">CIN: ${s.cin || "Pending"}</span></div>
      <div class="mca-grid">
        <div><b>Incorporated:</b> ${s.incorporation_date || "-"}</div><div><b>ROC:</b> ${s.roc || "-"}</div>
        <div><b>Authorized Capital:</b> ${s.authorized_capital || "-"}</div><div><b>Paid-up Capital:</b> ${s.paid_up_capital || "-"}</div>
        ${s.pan ? `<div><b>PAN:</b> ${s.pan}</div>` : ""}${s.tan ? `<div><b>TAN:</b> ${s.tan}</div>` : ""}
        <div style="grid-column:1/-1;"><b>Registered Address:</b> ${s.registered_address || "-"}</div>
      </div>
      ${dirsRows ? `<div class="table-responsive" style="margin-top:0.75rem;"><table><thead><tr><th>Director Name</th><th>DIN</th><th>Designation</th><th>Appointed</th></tr></thead><tbody>${dirsRows}</tbody></table></div>` : ""}
    `;
  } else {
    mcaCard.innerHTML = `<h3 style="color:var(--purple);font-size:0.95rem;">🌱 Pre-Incubation Track (Non-Pvt. Ltd.)</h3><p style="font-size:0.84rem;color:var(--text-muted);margin-top:0.3rem;">Categorized under SAKEC TBI Pre-Incubation. Add CIN/DIN via <b>Edit Startup Profile</b> upon MCA incorporation.</p>`;
  }

  document.getElementById("dtValueProp").textContent = dt.value_proposition || s.tagline;
  document.getElementById("dtBizModel").innerHTML = typeof dt.business_model === "object" && dt.business_model
    ? `<b>Model:</b> ${dt.business_model.model || "-"}<br><b>Pricing:</b> ${dt.business_model.pricing || "-"}<br><b>Channels:</b> ${dt.business_model.channels || "-"}` : "-";
  document.getElementById("dtTargetMarket").textContent = dt.target_market || "-";
  document.getElementById("dtTechStack").textContent = dt.tech_stack || "-";
  document.getElementById("dtSalesPipeline").textContent = dt.sales_pipeline_stage || "-";
  document.getElementById("dtRisk").textContent = dt.risk_assessment || "-";
  document.getElementById("dtTeamStructure").innerHTML = Array.isArray(dt.team_structure) ? dt.team_structure.map(m => `• <b>${m.name}</b> — ${m.role} (${m.dept})`).join("<br>") : s.founder_name;
  document.getElementById("dtRoadmap").innerHTML = Array.isArray(dt.product_roadmap) ? dt.product_roadmap.map(r => `<div style="margin-bottom:0.35rem;display:flex;justify-content:space-between;"><span><b>${r.q}:</b> ${r.item}</span><span class="badge ${r.status === "Completed" ? "badge-green" : "badge-blue"}">${r.status}</span></div>`).join("") : "-";
}

// INTERNS
async function loadInternsTable() {
  const stId = document.getElementById("internStartupFilter")?.value || "all";
  const sem = document.getElementById("internSemFilter")?.value || "all";
  const res = await apiCall(`/api/interns?year=${encodeURIComponent(YEAR_FILTER)}&startup_id=${encodeURIComponent(stId)}&semester=${encodeURIComponent(sem)}`);
  document.getElementById("internsTableBody").innerHTML = (res?.interns || []).map(i => `
    <tr>
      <td><b>${i.academic_year}</b><div style="font-size:0.74rem;color:var(--text-muted);">${i.semester}</div></td>
      <td><b>${i.startup_name}</b></td><td><b>${i.name}</b></td>
      <td><span class="badge ${i.role === "Founder" ? "badge-gold" : "badge-blue"}">${i.role}</span></td>
      <td>${i.student_class || "-"}<div style="font-size:0.74rem;color:var(--text-muted);">${i.department || "-"}</div></td>
      <td style="font-family:monospace;font-size:0.78rem;">${i.prn || "-"}</td>
      <td><div style="font-size:0.8rem;">${i.phone || "-"}</div><div style="font-size:0.74rem;color:var(--text-muted);">${i.email || "-"}</div></td>
      <td><div style="font-size:0.78rem;">${i.start_date || "-"} → ${i.end_date || "-"}</div></td>
    </tr>
  `).join("") || `<tr><td colspan="8" style="text-align:center;padding:1.5rem;color:var(--text-muted);">No records found.</td></tr>`;
}
function filterInternsTable() {
  const q = document.getElementById("internSearchInput").value.toLowerCase();
  document.querySelectorAll("#internsTableBody tr").forEach(r => r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none");
}
function openAddInternModal() { document.getElementById("addInternModal").classList.add("active"); }
async function handleSaveIntern(e) {
  e.preventDefault();
  const res = await apiCall("/api/interns", "POST", {
    startup_id: parseInt(document.getElementById("addInternStartup").value),
    academic_year: document.getElementById("addInternYear").value,
    semester: document.getElementById("addInternSem").value,
    name: document.getElementById("addInternName").value,
    role: document.getElementById("addInternRole").value,
    student_class: document.getElementById("addInternClass").value,
    department: document.getElementById("addInternDept").value,
    prn: document.getElementById("addInternPRN").value,
    phone: document.getElementById("addInternPhone").value,
    email: document.getElementById("addInternEmail").value,
    start_date: document.getElementById("addInternStart").value,
    end_date: document.getElementById("addInternEnd").value
  });
  if (res && res.status === "intern_added") { closeModal("addInternModal"); await loadInternsTable(); await loadPortfolioData(); }
}

// USERS & ADMIN ACCOUNTS
async function loadUsersTable() {
  if (CURRENT_USER.role !== "faculty_incharge") return;
  const res = await apiCall("/api/users");
  document.getElementById("usersTableBody").innerHTML = (res?.users || []).map(u => `
    <tr>
      <td style="font-family:monospace;font-weight:700;">${u.username}</td>
      <td><b>${u.full_name}</b></td>
      <td><span class="badge ${u.role === "faculty_incharge" ? "badge-gold" : (u.role === "founder" ? "badge-green" : "badge-blue")}">${u.role}</span></td>
      <td>${u.designation || "-"}${u.startup_name ? `<div style="font-size:0.74rem;color:var(--primary);">${u.startup_name}</div>` : ""}</td>
      <td>${u.email}</td>
      <td style="white-space:nowrap;">
        <button class="btn btn-outline btn-sm" onclick="resetUserPassword(${u.id},'${u.username}')">🔑 Reset Pwd</button>
        ${u.id !== CURRENT_USER.id ? `<button class="btn btn-outline btn-sm" style="color:var(--danger);" onclick="deleteUser(${u.id},'${u.username}')">✕</button>` : ""}
      </td>
    </tr>
  `).join("");
}
function openCreateUserModal() { document.getElementById("createUserModal").classList.add("active"); }
async function handleCreateUser(e) {
  e.preventDefault();
  const res = await apiCall("/api/users", "POST", {
    username: document.getElementById("cuUsername").value,
    password: document.getElementById("cuPassword").value,
    full_name: document.getElementById("cuFullName").value,
    email: document.getElementById("cuEmail").value,
    role: document.getElementById("cuRole").value,
    designation: document.getElementById("cuDesig").value,
    startup_id: document.getElementById("cuStartup").value || null
  });
  if (res && res.status === "user_created") {
    alert(`Account '${res.username}' created successfully!`);
    closeModal("createUserModal");
    await loadUsersTable();
  } else {
    alert(res?.error || "Failed to create account.");
  }
}
async function resetUserPassword(uid, uname) {
  const pwd = prompt(`Enter new password for ${uname}:`, "Sakec@123");
  if (!pwd) return;
  const res = await apiCall(`/api/users/${uid}`, "PUT", { new_password: pwd });
  if (res && res.status === "user_updated") alert(`Password reset for ${uname}.`);
}
async function deleteUser(uid, uname) {
  if (!confirm(`Delete account '${uname}'?`)) return;
  await apiCall(`/api/users/${uid}`, "DELETE");
  await loadUsersTable();
}

// EDIT STARTUP PROFILE & DIGITAL TWIN
async function openEditStartupProfileModal(id = null) {
  CURRENT_STARTUP_ID = id ? parseInt(id) : CURRENT_STARTUP_ID;
  const sRes = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}`);
  if (!sRes || !sRes.startup) return;
  const s = sRes.startup;
  document.getElementById("editStName").value = s.name;
  document.getElementById("editStTagline").value = s.tagline;
  document.getElementById("editStTrack").value = s.incubation_type;
  document.getElementById("editStYears").value = s.active_years;
  document.getElementById("editStCIN").value = s.cin || "";
  document.getElementById("editStIncDate").value = s.incorporation_date || "";
  document.getElementById("editStDept").value = s.department;
  document.getElementById("editStFounder").value = s.founder_name;
  document.getElementById("editStEmail").value = s.founder_email;
  document.getElementById("editStPhase").value = s.current_phase;
  document.getElementById("editStStage").value = s.stage;
  document.getElementById("editStHealth").value = s.health_score;
  document.getElementById("editStRev").value = s.monthly_revenue;
  document.getElementById("editStBurn").value = s.monthly_burn;
  document.getElementById("editStCash").value = s.cash_in_bank;
  document.getElementById("editStOdUrl").value = s.onedrive_folder_url || "";
  document.getElementById("editStAddress").value = s.registered_address || "";
  document.getElementById("editStartupModal").classList.add("active");
}
async function handleSaveStartupProfile(e) {
  e.preventDefault();
  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}`, "PUT", {
    name: document.getElementById("editStName").value, tagline: document.getElementById("editStTagline").value,
    incubation_type: document.getElementById("editStTrack").value, active_years: document.getElementById("editStYears").value,
    cin: document.getElementById("editStCIN").value, incorporation_date: document.getElementById("editStIncDate").value,
    department: document.getElementById("editStDept").value, founder_name: document.getElementById("editStFounder").value,
    founder_email: document.getElementById("editStEmail").value, current_phase: parseInt(document.getElementById("editStPhase").value),
    stage: document.getElementById("editStStage").value, health_score: parseInt(document.getElementById("editStHealth").value),
    monthly_revenue: parseFloat(document.getElementById("editStRev").value), monthly_burn: parseFloat(document.getElementById("editStBurn").value),
    cash_in_bank: parseFloat(document.getElementById("editStCash").value), onedrive_folder_url: document.getElementById("editStOdUrl").value,
    registered_address: document.getElementById("editStAddress").value
  });
  if (res && res.status === "startup_updated") { closeModal("editStartupModal"); await loadAllStartupsForDropdowns(); await refreshActiveView(); }
}

function openEditDigitalTwinModal() {
  document.getElementById("editDtValueProp").value = document.getElementById("dtValueProp").textContent;
  document.getElementById("editDtTargetMarket").value = document.getElementById("dtTargetMarket").textContent;
  document.getElementById("editDtSalesPipeline").value = document.getElementById("dtSalesPipeline").textContent;
  document.getElementById("editDtTechStack").value = document.getElementById("dtTechStack").textContent;
  document.getElementById("editDtRisk").value = document.getElementById("dtRisk").textContent;
  document.getElementById("editDtModal").classList.add("active");
}
async function handleSaveDigitalTwin(e) {
  e.preventDefault();
  await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/digital-twin`, "PUT", {
    value_proposition: document.getElementById("editDtValueProp").value, target_market: document.getElementById("editDtTargetMarket").value,
    sales_pipeline_stage: document.getElementById("editDtSalesPipeline").value, tech_stack: document.getElementById("editDtTechStack").value,
    risk_assessment: document.getElementById("editDtRisk").value
  });
  closeModal("editDtModal");
  await loadDigitalTwin(CURRENT_STARTUP_ID);
}

// USIM, MILESTONES, MENTORSHIP, ONBOARDING
function updateSimFromSliders() {
  ["BasePrice","FixedCost","VarCost","Marketing","CAC"].forEach(k => document.getElementById("val"+k).textContent = "₹" + Number(document.getElementById("sim"+k).value).toLocaleString("en-IN"));
  document.getElementById("valGrowth").textContent = document.getElementById("simGrowth").value + "%";
  document.getElementById("valChurn").textContent = document.getElementById("simChurn").value + "%";
  runSimulation();
}
async function prefillSimulator(id) {
  CURRENT_STARTUP_ID = parseInt(id);
  const s = (await apiCall(`/api/startups/${id}`))?.startup;
  if (s) { document.getElementById("simCash").value = s.cash_in_bank || 300000; document.getElementById("simCustomers").value = Math.max(1, s.customer_count || 5); document.getElementById("simFixedCost").value = Math.max(2000, s.monthly_burn || 30000); }
  updateSimFromSliders();
}
async function runSimulation() {
  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/simulate`, "POST", {
    base_price: +document.getElementById("simBasePrice").value, monthly_fixed_cost: +document.getElementById("simFixedCost").value,
    variable_cost_per_unit: +document.getElementById("simVarCost").value, marketing_spend: +document.getElementById("simMarketing").value,
    cac: +document.getElementById("simCAC").value, organic_growth_rate: +document.getElementById("simGrowth").value,
    churn_rate: +document.getElementById("simChurn").value, initial_cash: +document.getElementById("simCash").value,
    initial_customers: +document.getElementById("simCustomers").value
  });
  if (!res || !res.summary) return;
  LATEST_SIMULATION_RESULT = res;
  const s = res.summary;
  document.getElementById("simOutMargin").textContent = "₹" + Number(s.contribution_margin).toLocaleString("en-IN");
  document.getElementById("simOutMarginPct").textContent = `${s.margin_percentage}%`;
  document.getElementById("simOutLtvCac").textContent = `${s.ltv_cac_ratio}x`;
  document.getElementById("simOutBreakEven").textContent = typeof s.break_even_month === "number" ? `Month ${s.break_even_month}` : s.break_even_month;
  document.getElementById("simOutARR").textContent = "₹" + Number(s.projected_arr).toLocaleString("en-IN");
  document.getElementById("simOutRunway").textContent = `Runway: ${s.runway_months} mos`;
  document.getElementById("simTableBody").innerHTML = res.monthly_projections.map(m => `<tr><td>M${m.month}</td><td>${m.customers}</td><td>₹${Number(m.revenue).toLocaleString("en-IN")}</td><td>₹${Number(m.total_expenses).toLocaleString("en-IN")}</td><td style="color:${m.net_cash_flow>=0?'#10b981':'#ef4444'};">₹${Number(m.net_cash_flow).toLocaleString("en-IN")}</td><td><b>₹${Number(m.cash_balance).toLocaleString("en-IN")}</b></td></tr>`).join("");
  const c = document.getElementById("simChartContainer"), w = c.clientWidth || 560, h = 185, p = 26;
  const mx = Math.max(...res.monthly_projections.map(x => Math.max(x.revenue, x.total_expenses)), 10000);
  const rPts = res.monthly_projections.map((x,i) => `${p+(i/11)*(w-2*p)},${h-p-(x.revenue/mx)*(h-2*p)}`).join(" ");
  const ePts = res.monthly_projections.map((x,i) => `${p+(i/11)*(w-2*p)},${h-p-(x.total_expenses/mx)*(h-2*p)}`).join(" ");
  c.innerHTML = `<svg width="100%" height="${h}" viewBox="0 0 ${w} ${h}"><polyline fill="none" stroke="#10b981" stroke-width="3" points="${rPts}"/><polyline fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5" points="${ePts}"/></svg>`;
}
async function saveCurrentSimulation() {
  if (!LATEST_SIMULATION_RESULT) return;
  const name = prompt("Scenario name:", "USim Scenario");
  if (!name) return;
  await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/save-simulation`, "POST", {
    scenario_name: name, base_price: +document.getElementById("simBasePrice").value, monthly_fixed_cost: +document.getElementById("simFixedCost").value,
    variable_cost_per_unit: +document.getElementById("simVarCost").value, marketing_spend: +document.getElementById("simMarketing").value,
    organic_growth_rate: +document.getElementById("simGrowth").value, churn_rate: +document.getElementById("simChurn").value,
    runway_months: LATEST_SIMULATION_RESULT.summary.runway_months, break_even_month: typeof LATEST_SIMULATION_RESULT.summary.break_even_month === "number" ? LATEST_SIMULATION_RESULT.summary.break_even_month : 12,
    projected_arr: LATEST_SIMULATION_RESULT.summary.projected_arr
  });
  alert("Simulation saved!");
}

async function loadMilestones(id) {
  CURRENT_STARTUP_ID = parseInt(id);
  const [mRes, kRes] = await Promise.all([apiCall(`/api/startups/${id}/milestones`), apiCall(`/api/startups/${id}/kpis`)]);
  document.getElementById("milestonesTableBody").innerHTML = (mRes?.milestones || []).map(m => `
    <tr><td><span class="badge badge-blue">Phase ${m.phase}</span></td><td><b>${m.title}</b></td><td>${m.target_date}</td><td><span class="badge ${m.status==='Verified'?'badge-green':'badge-blue'}">${m.status}</span></td><td>${m.verification_notes||'-'}</td>
    <td>${["faculty_incharge","mentor"].includes(CURRENT_USER.role) && m.status !== "Verified" ? `<button class="btn btn-accent btn-sm" onclick="verifyMilestone(${m.id})">✓ Verify</button>` : "-"}</td></tr>
  `).join("");
  document.getElementById("kpiTableBody").innerHTML = (kRes?.kpis || []).map(k => `<tr><td><b>${k.month}</b></td><td>₹${Number(k.revenue).toLocaleString("en-IN")}</td><td>₹${Number(k.burn_rate).toLocaleString("en-IN")}</td><td>${k.paying_customers}</td><td>${k.active_users}</td><td>${k.notes||''}</td></tr>`).join("");
}
async function verifyMilestone(id) {
  const notes = prompt("Remarks:", "Verified by Dr. Rohan Borgalli");
  if (notes === null) return;
  await apiCall(`/api/milestones/${id}`, "PUT", { status: "Verified", verification_notes: notes, completion_date: new Date().toISOString().split("T")[0] });
  loadMilestones(CURRENT_STARTUP_ID);
}
function openAddMilestoneModal() { document.getElementById("addMilestoneModal").classList.add("active"); }
async function handleSaveNewMilestone(e) {
  e.preventDefault();
  await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/milestones`, "POST", { title: document.getElementById("newMilestoneTitle").value, phase: +document.getElementById("newMilestonePhase").value, target_date: document.getElementById("newMilestoneDate").value });
  closeModal("addMilestoneModal"); loadMilestones(CURRENT_STARTUP_ID);
}
function openLogKPIModal() { document.getElementById("logKpiModal").classList.add("active"); }
async function handleSaveKPI(e) {
  e.preventDefault();
  await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/kpis`, "POST", { month: document.getElementById("kpiMonth").value, revenue: +document.getElementById("kpiRevenue").value, burn_rate: +document.getElementById("kpiBurn").value, paying_customers: +document.getElementById("kpiCustomers").value, active_users: +document.getElementById("kpiUsers").value, notes: document.getElementById("kpiNotes").value });
  closeModal("logKpiModal"); loadMilestones(CURRENT_STARTUP_ID);
}
async function loadMentorshipReviews() {
  const res = await apiCall("/api/mentorship-all");
  document.getElementById("mentorshipTableBody").innerHTML = (res?.sessions || []).map(s => `<tr><td>${s.session_date}</td><td><b>${s.startup_name}</b></td><td>${s.mentor_name}</td><td>${s.focus_area}</td><td>${"⭐".repeat(s.health_rating)}</td><td>${s.feedback}</td><td>${s.action_items||'-'}</td></tr>`).join("");
}
function openLogMentorshipModal() { document.getElementById("mentorshipModal").classList.add("active"); }
async function handleSaveMentorship(e) {
  e.preventDefault();
  await apiCall("/api/mentorship", "POST", { startup_id: +document.getElementById("mentorStartupSelect").value, mentor_name: document.getElementById("mentorName").value, focus_area: document.getElementById("mentorFocus").value, health_rating: +document.getElementById("mentorRating").value, feedback: document.getElementById("mentorFeedback").value, action_items: document.getElementById("mentorActions").value });
  closeModal("mentorshipModal"); loadMentorshipReviews();
}

async function handleOnboardStartup(e) {
  e.preventDefault();
  const res = await apiCall("/api/startups", "POST", {
    name: document.getElementById("newStartupName").value,
    academic_year: document.getElementById("newStartupYear").value,
    active_years: document.getElementById("newStartupYear").value,
    incubation_type: document.getElementById("newStartupTrack").value,
    cin: document.getElementById("newStartupCIN").value,
    department: document.getElementById("newStartupDept").value,
    founder_name: document.getElementById("newStartupFounder").value,
    founder_email: document.getElementById("newStartupEmail").value,
    founder_phone: document.getElementById("newStartupPhone").value,
    onedrive_folder_url: document.getElementById("newStartupOdUrl").value,
    founder_username: document.getElementById("newFounderUser").value,
    founder_password: document.getElementById("newFounderPass").value,
    tagline: document.getElementById("newStartupTagline").value
  });
  if (res && res.status === "success") {
    alert(`Startup onboarded! Founder login '${res.founder_username}' and OneDrive document checklist have been created.`);
    document.getElementById("onboardStartupForm").reset();
    await loadAllStartupsForDropdowns();
    await refreshActiveView();
    switchTab("tab-portfolio");
  } else {
    alert(res?.error || "Onboarding failed.");
  }
}
