/**
 * SAKEC Technology Business Incubator (TBI) Platform
 * Frontend Interactive Controller & Visualization Engine
 * Developed by Dr. Rohan Appasaheb Borgalli
 */

// Global State
let CURRENT_USER = null;
let AUTH_TOKEN = localStorage.getItem("sakec_token") || null;
let STARTUPS = [];
let CURRENT_STARTUP_ID = 1;
let LATEST_SIMULATION_RESULT = null;

// Lifecycle Phase Definitions
const PHASES = [
  { id: 1, name: "Selection & Digital Onboarding", month: "Month 1" },
  { id: 2, name: "Simulation & Strategic Planning", month: "Month 2" },
  { id: 3, name: "Operational Deployment (WorkOS)", month: "Months 3-4" },
  { id: 4, name: "Mentorship & Incubation Monitoring", month: "Month 5" },
  { id: 5, name: "Investor Readiness & Graduation", month: "Month 6" }
];

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  checkAuth();
  await loadInitialData();
  setupSimulationSliders();
  renderLifecycleFunnel();
});

// API Helper
async function apiCall(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (AUTH_TOKEN) {
    headers["Authorization"] = `Bearer ${AUTH_TOKEN}`;
  }
  const config = { method, headers };
  if (body) config.body = JSON.stringify(body);

  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401 && endpoint !== "/api/login") {
      logout();
      return null;
    }
    return await res.json();
  } catch (err) {
    console.error("API Call Error:", endpoint, err);
    return null;
  }
}

// Auth Handling
async function checkAuth() {
  if (AUTH_TOKEN) {
    const res = await apiCall("/api/me");
    if (res && res.user) {
      setCurrentUser(res.user);
      return;
    }
  }
  setCurrentUser(null);
}

function setCurrentUser(user) {
  CURRENT_USER = user;
  const display = document.getElementById("currentUserDisplay");
  const authBtn = document.getElementById("authBtn");

  if (user) {
    display.textContent = `${user.full_name} (${formatRole(user.role)})`;
    authBtn.textContent = "Logout";
    authBtn.onclick = logout;
  } else {
    display.textContent = "Viewing as: Guest (Read-Only)";
    authBtn.textContent = "Login";
    authBtn.onclick = openLoginModal;
  }
}

function formatRole(role) {
  switch (role) {
    case "faculty_incharge": return "Faculty Incharge (Admin)";
    case "authority": return "College Authority";
    case "mentor": return "Incubation Mentor";
    case "founder": return "Startup Founder";
    default: return role;
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;

  const res = await apiCall("/api/login", "POST", { username, password });
  if (res && res.token) {
    AUTH_TOKEN = res.token;
    localStorage.setItem("sakec_token", AUTH_TOKEN);
    setCurrentUser(res.user);
    closeLoginModal();
    await loadInitialData();
  } else {
    alert("Invalid credentials. Please check username or password.");
  }
}

async function quickLogin(u, p) {
  document.getElementById("loginUsername").value = u;
  document.getElementById("loginPassword").value = p;
  const res = await apiCall("/api/login", "POST", { username: u, password: p });
  if (res && res.token) {
    AUTH_TOKEN = res.token;
    localStorage.setItem("sakec_token", AUTH_TOKEN);
    setCurrentUser(res.user);
    closeLoginModal();
    await loadInitialData();
  }
}

function logout() {
  apiCall("/api/logout", "POST");
  AUTH_TOKEN = null;
  localStorage.removeItem("sakec_token");
  setCurrentUser(null);
  loadInitialData();
}

function openLoginModal() { document.getElementById("loginModal").classList.add("active"); }
function closeLoginModal() { document.getElementById("loginModal").classList.remove("active"); }

// Navigation Tabs
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach(b => b.classList.remove("active"));

  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  const tabBtns = document.querySelectorAll(".nav-tab");
  tabBtns.forEach(btn => {
    if (btn.getAttribute("onclick").includes(tabId)) {
      btn.classList.add("active");
    }
  });

  if (tabId === "tab-digital-twin") loadDigitalTwin(CURRENT_STARTUP_ID);
  if (tabId === "tab-usim") prefillSimulator(CURRENT_STARTUP_ID);
  if (tabId === "tab-milestones") loadMilestones(CURRENT_STARTUP_ID);
  if (tabId === "tab-mentorship") loadMentorshipReviews();
}

// Initial Data Load
async function loadInitialData() {
  await loadStartups();
  await loadPortfolioAnalytics();
}

async function loadStartups() {
  const res = await apiCall("/api/startups");
  if (!res || !res.startups) return;
  STARTUPS = res.startups;

  // Populate Select Boxes
  const dtSelect = document.getElementById("dtStartupSelect");
  const usimSelect = document.getElementById("usimStartupSelect");
  const msSelect = document.getElementById("milestoneStartupSelect");
  const mentorSelect = document.getElementById("mentorStartupSelect");

  [dtSelect, usimSelect, msSelect, mentorSelect].forEach(sel => {
    if (!sel) return;
    sel.innerHTML = "";
    STARTUPS.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} (${s.department})`;
      sel.appendChild(opt);
    });
  });

  // If user is a founder, lock to their startup
  if (CURRENT_USER && CURRENT_USER.role === "founder" && CURRENT_USER.startup_id) {
    CURRENT_STARTUP_ID = CURRENT_USER.startup_id;
    if (dtSelect) dtSelect.value = CURRENT_STARTUP_ID;
    if (usimSelect) usimSelect.value = CURRENT_STARTUP_ID;
    if (msSelect) msSelect.value = CURRENT_STARTUP_ID;
  }

  renderPortfolioTable();
  document.getElementById("diagActiveStartups").textContent = STARTUPS.length;
}

// Portfolio Analytics
async function loadPortfolioAnalytics() {
  const res = await apiCall("/api/analytics/portfolio");
  if (!res || !res.summary) return;
  const sum = res.summary;

  document.getElementById("kpiTotalStartups").textContent = sum.total_startups;
  document.getElementById("kpiTotalRevenue").textContent = "₹" + Number(sum.total_monthly_revenue).toLocaleString('en-IN');
  document.getElementById("kpiAvgHealth").textContent = `${sum.avg_health_score}/100`;
  document.getElementById("kpiTotalClients").textContent = sum.total_paying_clients;
  document.getElementById("kpiTotalJobs").textContent = sum.total_team_members;

  renderLifecycleFunnel(sum.phase_distribution);
}

// Render Funnel
function renderLifecycleFunnel(distribution = {}) {
  const container = document.getElementById("lifecycleStepsContainer");
  if (!container) return;
  container.innerHTML = "";

  PHASES.forEach(p => {
    const count = distribution[p.id] || 0;
    const div = document.createElement("div");
    div.className = `phase-step ${count > 0 ? 'active' : ''}`;
    div.innerHTML = `
      <div class="phase-num">Phase ${p.id} (${p.month})</div>
      <div class="phase-name">${p.name}</div>
      <div class="phase-count"><b>${count}</b> Startup${count === 1 ? '' : 's'} Active</div>
    `;
    container.appendChild(div);
  });
}

// Render Portfolio Table
function renderPortfolioTable() {
  const tbody = document.getElementById("portfolioTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  STARTUPS.forEach(s => {
    const tr = document.createElement("tr");

    let healthBadge = "badge-green";
    if (s.health_score < 80) healthBadge = "badge-gold";
    if (s.health_score < 70) healthBadge = "badge-red";

    tr.innerHTML = `
      <td>
        <b>${s.name}</b><br>
        <span style="font-size: 0.75rem; color: var(--text-muted);">${s.stage}</span>
      </td>
      <td>${s.department}</td>
      <td>${s.founder_name}</td>
      <td><span class="badge badge-blue">Phase ${s.current_phase}</span></td>
      <td><span class="badge ${healthBadge}">${s.health_score}/100</span></td>
      <td>₹${Number(s.monthly_revenue).toLocaleString('en-IN')}</td>
      <td><b>${s.runway_months}</b> mos</td>
      <td>${s.customer_count}</td>
      <td><span class="badge badge-gold">${s.investor_readiness_score}%</span></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="viewStartupDetail(${s.id})">360° View</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterPortfolioTable() {
  const query = document.getElementById("portfolioSearchInput").value.toLowerCase();
  const rows = document.querySelectorAll("#portfolioTableBody tr");
  rows.forEach(r => {
    const text = r.textContent.toLowerCase();
    r.style.display = text.includes(query) ? "" : "none";
  });
}

function viewStartupDetail(id) {
  CURRENT_STARTUP_ID = id;
  const dtSelect = document.getElementById("dtStartupSelect");
  if (dtSelect) dtSelect.value = id;
  switchTab("tab-digital-twin");
}

function exportPortfolioCSV() {
  window.open("/api/export/csv", "_blank");
}

// WorkOS Business Digital Twin
async function loadDigitalTwin(startupId) {
  CURRENT_STARTUP_ID = parseInt(startupId);
  const sRes = await apiCall(`/api/startups/${startupId}`);
  const dtRes = await apiCall(`/api/startups/${startupId}/digital-twin`);

  if (!sRes || !sRes.startup || !dtRes || !dtRes.digital_twin) return;
  const s = sRes.startup;
  const dt = dtRes.digital_twin;

  document.getElementById("digitalTwinHeader").innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
      <div>
        <h2 style="color: var(--primary); font-size: 1.3rem;">${s.name}</h2>
        <div style="color: var(--text-muted); font-size: 0.85rem;">${s.tagline}</div>
        <div style="margin-top: 0.35rem;">
          <span class="badge badge-blue">Phase ${s.current_phase}: ${PHASES[s.current_phase - 1].name}</span>
          <span class="badge badge-green">Health: ${s.health_score}/100</span>
          <span class="badge badge-gold">Investor Readiness: ${s.investor_readiness_score}%</span>
        </div>
      </div>
      <div style="text-align: right; font-size: 0.85rem;">
        <b>Monthly Revenue:</b> ₹${Number(s.monthly_revenue).toLocaleString('en-IN')}<br>
        <b>Monthly Burn:</b> ₹${Number(s.monthly_burn).toLocaleString('en-IN')} | <b>Runway:</b> ${s.runway_months} mos<br>
        <b>Founders:</b> ${s.founder_name} (${s.founder_email})
      </div>
    </div>
  `;

  document.getElementById("dtValueProp").textContent = dt.value_proposition || "N/A";
  
  // Biz model
  let bmHtml = "";
  if (typeof dt.business_model === 'object' && dt.business_model !== null) {
    bmHtml = `<b>Model:</b> ${dt.business_model.model || 'Standard'}<br>
              <b>Pricing:</b> ${dt.business_model.pricing || 'TBD'}<br>
              <b>Channels:</b> ${dt.business_model.channels || 'Direct Sales'}`;
  } else {
    bmHtml = dt.business_model || "To be formulated in Phase 2 USim";
  }
  document.getElementById("dtBizModel").innerHTML = bmHtml;

  document.getElementById("dtTargetMarket").textContent = dt.target_market || "N/A";
  document.getElementById("dtTechStack").textContent = dt.tech_stack || "N/A";
  document.getElementById("dtSalesPipeline").textContent = dt.sales_pipeline_stage || "N/A";
  document.getElementById("dtRisk").textContent = dt.risk_assessment || "N/A";

  // Team
  let teamHtml = "";
  if (Array.isArray(dt.team_structure)) {
    dt.team_structure.forEach(m => {
      teamHtml += `• <b>${m.name}</b> (${m.role} - ${m.dept})<br>`;
    });
  } else {
    teamHtml = dt.team_structure || s.founder_name;
  }
  document.getElementById("dtTeamStructure").innerHTML = teamHtml;

  // Roadmap
  let rmHtml = "";
  if (Array.isArray(dt.product_roadmap)) {
    dt.product_roadmap.forEach(r => {
      let bClass = r.status === 'Completed' ? 'badge-green' : (r.status === 'In Progress' ? 'badge-blue' : 'badge-gray');
      rmHtml += `<div style="margin-bottom: 0.4rem; display: flex; justify-content: space-between;">
                   <span><b>${r.q}:</b> ${r.item}</span>
                   <span class="badge ${bClass}">${r.status}</span>
                 </div>`;
    });
  } else {
    rmHtml = dt.product_roadmap || "Roadmap under drafting";
  }
  document.getElementById("dtRoadmap").innerHTML = rmHtml;
}

function openEditDigitalTwinModal() {
  document.getElementById("editDtValueProp").value = document.getElementById("dtValueProp").textContent;
  document.getElementById("editDtTargetMarket").value = document.getElementById("dtTargetMarket").textContent;
  document.getElementById("editDtSalesPipeline").value = document.getElementById("dtSalesPipeline").textContent;
  document.getElementById("editDtTechStack").value = document.getElementById("dtTechStack").textContent;
  document.getElementById("editDtRisk").value = document.getElementById("dtRisk").textContent;
  document.getElementById("editDtModal").classList.add("active");
}
function closeEditDigitalTwinModal() { document.getElementById("editDtModal").classList.remove("active"); }

async function handleSaveDigitalTwin(e) {
  e.preventDefault();
  const payload = {
    value_proposition: document.getElementById("editDtValueProp").value,
    target_market: document.getElementById("editDtTargetMarket").value,
    sales_pipeline_stage: document.getElementById("editDtSalesPipeline").value,
    tech_stack: document.getElementById("editDtTechStack").value,
    risk_assessment: document.getElementById("editDtRisk").value
  };

  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/digital-twin`, "PUT", payload);
  if (res && res.status === "digital_twin_updated") {
    closeEditDigitalTwinModal();
    loadDigitalTwin(CURRENT_STARTUP_ID);
  } else {
    alert("Failed to update digital twin. Ensure you have proper permissions.");
  }
}

// USim Startup Decision Simulator
function setupSimulationSliders() {
  updateSimFromSliders();
}

function updateSimFromSliders() {
  const p = document.getElementById("simBasePrice").value;
  const fc = document.getElementById("simFixedCost").value;
  const vc = document.getElementById("simVarCost").value;
  const m = document.getElementById("simMarketing").value;
  const cac = document.getElementById("simCAC").value;
  const g = document.getElementById("simGrowth").value;
  const ch = document.getElementById("simChurn").value;

  document.getElementById("valBasePrice").textContent = "₹" + Number(p).toLocaleString('en-IN');
  document.getElementById("valFixedCost").textContent = "₹" + Number(fc).toLocaleString('en-IN');
  document.getElementById("valVarCost").textContent = "₹" + Number(vc).toLocaleString('en-IN');
  document.getElementById("valMarketing").textContent = "₹" + Number(m).toLocaleString('en-IN');
  document.getElementById("valCAC").textContent = "₹" + Number(cac).toLocaleString('en-IN');
  document.getElementById("valGrowth").textContent = `${g}%`;
  document.getElementById("valChurn").textContent = `${ch}%`;

  runSimulation();
}

async function prefillSimulator(startupId) {
  CURRENT_STARTUP_ID = parseInt(startupId);
  const sRes = await apiCall(`/api/startups/${startupId}`);
  if (!sRes || !sRes.startup) return;
  const s = sRes.startup;

  document.getElementById("simCash").value = s.cash_in_bank;
  document.getElementById("simCustomers").value = s.customer_count;
  document.getElementById("simFixedCost").value = Math.max(10000, s.monthly_burn);

  updateSimFromSliders();
  loadSavedSimulations(startupId);
}

async function runSimulation() {
  const payload = {
    base_price: parseFloat(document.getElementById("simBasePrice").value),
    monthly_fixed_cost: parseFloat(document.getElementById("simFixedCost").value),
    variable_cost_per_unit: parseFloat(document.getElementById("simVarCost").value),
    marketing_spend: parseFloat(document.getElementById("simMarketing").value),
    cac: parseFloat(document.getElementById("simCAC").value),
    organic_growth_rate: parseFloat(document.getElementById("simGrowth").value),
    churn_rate: parseFloat(document.getElementById("simChurn").value),
    initial_cash: parseFloat(document.getElementById("simCash").value),
    initial_customers: parseInt(document.getElementById("simCustomers").value)
  };

  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/simulate`, "POST", payload);
  if (!res || !res.summary) return;
  LATEST_SIMULATION_RESULT = res;

  const sum = res.summary;
  document.getElementById("simOutMargin").textContent = "₹" + Number(sum.contribution_margin).toLocaleString('en-IN');
  document.getElementById("simOutMarginPct").textContent = `${sum.margin_percentage}% contribution margin`;
  document.getElementById("simOutLtvCac").textContent = `${sum.ltv_cac_ratio}x`;
  document.getElementById("simOutBreakEven").textContent = typeof sum.break_even_month === 'number' ? `Month ${sum.break_even_month}` : sum.break_even_month;
  document.getElementById("simOutARR").textContent = "₹" + Number(sum.projected_arr).toLocaleString('en-IN');
  document.getElementById("simOutRunway").textContent = `Runway: ${sum.runway_months} mos`;

  // Render Table
  const tbody = document.getElementById("simTableBody");
  tbody.innerHTML = "";
  res.monthly_projections.forEach(m => {
    const tr = document.createElement("tr");
    const flowColor = m.net_cash_flow >= 0 ? "color: #10b981; font-weight: 600;" : "color: #ef4444;";
    tr.innerHTML = `
      <td><b>Month ${m.month}</b></td>
      <td>${m.customers}</td>
      <td>₹${Number(m.revenue).toLocaleString('en-IN')}</td>
      <td>₹${Number(m.fixed_cost).toLocaleString('en-IN')}</td>
      <td>₹${Number(m.variable_cost).toLocaleString('en-IN')}</td>
      <td>₹${Number(m.marketing_spend).toLocaleString('en-IN')}</td>
      <td>₹${Number(m.total_expenses).toLocaleString('en-IN')}</td>
      <td style="${flowColor}">₹${Number(m.net_cash_flow).toLocaleString('en-IN')}</td>
      <td><b>₹${Number(m.cash_balance).toLocaleString('en-IN')}</b></td>
    `;
    tbody.appendChild(tr);
  });

  renderSimulationChart(res.monthly_projections);
}

function renderSimulationChart(projections) {
  const container = document.getElementById("simChartContainer");
  if (!container || !projections || projections.length === 0) return;

  const width = container.clientWidth || 600;
  const height = 200;
  const padding = 30;

  const maxRev = Math.max(...projections.map(p => Math.max(p.revenue, p.total_expenses)), 100000);
  const pointsRev = [];
  const pointsExp = [];

  projections.forEach((p, idx) => {
    const x = padding + (idx / (projections.length - 1)) * (width - 2 * padding);
    const yRev = height - padding - (p.revenue / maxRev) * (height - 2 * padding);
    const yExp = height - padding - (p.total_expenses / maxRev) * (height - 2 * padding);
    pointsRev.push(`${x},${yRev}`);
    pointsExp.push(`${x},${yExp}`);
  });

  container.innerHTML = `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow: visible;">
      <!-- Grid Lines -->
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#e5e7eb" stroke-width="1"/>
      <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4"/>
      
      <!-- Curves -->
      <polyline fill="none" stroke="#10b981" stroke-width="3" points="${pointsRev.join(' ')}" />
      <polyline fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,5" points="${pointsExp.join(' ')}" />

      <!-- Legend -->
      <text x="${padding}" y="15" fill="#10b981" font-size="12" font-weight="bold">● Monthly Revenue</text>
      <text x="${padding + 140}" y="15" fill="#ef4444" font-size="12" font-weight="bold">-- Total Monthly Expenses</text>
      <text x="${width - padding - 60}" y="15" fill="#6b7280" font-size="11">Peak: ₹${Math.round(maxRev).toLocaleString('en-IN')}</text>
    </svg>
  `;
}

async function saveCurrentSimulation() {
  if (!LATEST_SIMULATION_RESULT) return;
  const name = prompt("Enter scenario name for this USim simulation:", "Strategic Scale-up Scenario");
  if (!name) return;

  const payload = {
    scenario_name: name,
    base_price: parseFloat(document.getElementById("simBasePrice").value),
    monthly_fixed_cost: parseFloat(document.getElementById("simFixedCost").value),
    variable_cost_per_unit: parseFloat(document.getElementById("simVarCost").value),
    marketing_spend: parseFloat(document.getElementById("simMarketing").value),
    organic_growth_rate: parseFloat(document.getElementById("simGrowth").value),
    churn_rate: parseFloat(document.getElementById("simChurn").value),
    runway_months: LATEST_SIMULATION_RESULT.summary.runway_months,
    break_even_month: typeof LATEST_SIMULATION_RESULT.summary.break_even_month === 'number' ? LATEST_SIMULATION_RESULT.summary.break_even_month : 12,
    projected_arr: LATEST_SIMULATION_RESULT.summary.projected_arr,
    notes: "Saved via USim Interactive Simulator"
  };

  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/save-simulation`, "POST", payload);
  if (res && res.status === "simulation_saved") {
    alert("USim simulation scenario successfully saved!");
    loadSavedSimulations(CURRENT_STARTUP_ID);
  }
}

async function loadSavedSimulations(startupId) {
  const container = document.getElementById("savedSimsList");
  const res = await apiCall(`/api/startups/${startupId}/simulations`);
  if (!res || !res.simulations || res.simulations.length === 0) {
    container.innerHTML = "<p style='color: var(--text-muted); font-size: 0.85rem;'>No prior simulations logged for this venture.</p>";
    return;
  }

  let html = "<div style='display: flex; flex-direction: column; gap: 0.5rem;'>";
  res.simulations.forEach(s => {
    html += `
      <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: var(--radius); padding: 0.75rem; font-size: 0.85rem;">
        <div style="display: flex; justify-content: space-between;">
          <b>${s.scenario_name}</b>
          <span style="color: var(--text-muted);">${s.simulation_date}</span>
        </div>
        <div style="margin-top: 0.3rem; color: var(--text-muted);">
          Price: ₹${s.base_price} | Fixed Cost: ₹${s.monthly_fixed_cost}/mo | Break-even: M${s.break_even_month} | Projected ARR: ₹${Number(s.projected_arr).toLocaleString('en-IN')}
        </div>
      </div>
    `;
  });
  html += "</div>";
  container.innerHTML = html;
}

// Milestones & KPIs
async function loadMilestones(startupId) {
  CURRENT_STARTUP_ID = parseInt(startupId);
  const res = await apiCall(`/api/startups/${startupId}/milestones`);
  const tbody = document.getElementById("milestonesTableBody");
  tbody.innerHTML = "";

  if (!res || !res.milestones) return;
  res.milestones.forEach(m => {
    const tr = document.createElement("tr");

    let statusBadge = "badge-gray";
    if (m.status === "In Progress") statusBadge = "badge-blue";
    if (m.status === "Completed") statusBadge = "badge-gold";
    if (m.status === "Verified") statusBadge = "badge-green";

    let actionBtn = "";
    if (CURRENT_USER && (CURRENT_USER.role === "faculty_incharge" || CURRENT_USER.role === "authority" || CURRENT_USER.role === "mentor")) {
      if (m.status !== "Verified") {
        actionBtn = `<button class="btn btn-accent btn-sm" onclick="verifyMilestone(${m.id})">✓ Verify Milestone</button>`;
      } else {
        actionBtn = `<span style="color: #10b981; font-weight: 600;">✓ Verified</span>`;
      }
    } else if (CURRENT_USER && CURRENT_USER.role === "founder") {
      if (m.status !== "Verified") {
        actionBtn = `<button class="btn btn-outline btn-sm" onclick="markMilestoneComplete(${m.id})">Mark Completed</button>`;
      }
    }

    tr.innerHTML = `
      <td><span class="badge badge-blue">Phase ${m.phase}</span></td>
      <td><b>${m.title}</b></td>
      <td>${m.target_date}</td>
      <td><span class="badge ${statusBadge}">${m.status}</span></td>
      <td>${m.verification_notes || 'Pending formal review'}</td>
      <td>${actionBtn}</td>
    `;
    tbody.appendChild(tr);
  });

  loadKPIRecords(startupId);
}

async function verifyMilestone(id) {
  const notes = prompt("Enter verification remarks / mentor approval notes:", "Verified by Faculty Incharge Dr. Rohan Appasaheb Borgalli.");
  if (notes === null) return;

  const res = await apiCall(`/api/milestones/${id}`, "PUT", {
    status: "Verified",
    verification_notes: notes,
    completion_date: new Date().toISOString().split('T')[0]
  });

  if (res && res.status === "milestone_updated") {
    loadMilestones(CURRENT_STARTUP_ID);
    loadPortfolioAnalytics();
  }
}

async function markMilestoneComplete(id) {
  const res = await apiCall(`/api/milestones/${id}`, "PUT", {
    status: "Completed",
    completion_date: new Date().toISOString().split('T')[0]
  });
  if (res && res.status === "milestone_updated") {
    loadMilestones(CURRENT_STARTUP_ID);
  }
}

function openAddMilestoneModal() { document.getElementById("addMilestoneModal").classList.add("active"); }
function closeAddMilestoneModal() { document.getElementById("addMilestoneModal").classList.remove("active"); }

async function handleSaveNewMilestone(e) {
  e.preventDefault();
  const payload = {
    title: document.getElementById("newMilestoneTitle").value,
    phase: parseInt(document.getElementById("newMilestonePhase").value),
    target_date: document.getElementById("newMilestoneDate").value,
    status: "Pending"
  };

  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/milestones`, "POST", payload);
  if (res && res.status === "milestone_created") {
    closeAddMilestoneModal();
    loadMilestones(CURRENT_STARTUP_ID);
  }
}

async function loadKPIRecords(startupId) {
  const res = await apiCall(`/api/startups/${startupId}/kpis`);
  const tbody = document.getElementById("kpiTableBody");
  tbody.innerHTML = "";

  if (!res || !res.kpis) return;
  res.kpis.forEach(k => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><b>${k.month}</b></td>
      <td>₹${Number(k.revenue).toLocaleString('en-IN')}</td>
      <td>₹${Number(k.burn_rate).toLocaleString('en-IN')}</td>
      <td>${k.paying_customers}</td>
      <td>${k.active_users}</td>
      <td>₹${Number(k.cac).toLocaleString('en-IN')}</td>
      <td>₹${Number(k.ltv).toLocaleString('en-IN')}</td>
      <td>${k.notes || ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

function openLogKPIModal() { document.getElementById("logKpiModal").classList.add("active"); }
function closeLogKPIModal() { document.getElementById("logKpiModal").classList.remove("active"); }

async function handleSaveKPI(e) {
  e.preventDefault();
  const payload = {
    month: document.getElementById("kpiMonth").value,
    revenue: parseFloat(document.getElementById("kpiRevenue").value),
    burn_rate: parseFloat(document.getElementById("kpiBurn").value),
    paying_customers: parseInt(document.getElementById("kpiCustomers").value),
    active_users: parseInt(document.getElementById("kpiUsers").value),
    cac: parseFloat(document.getElementById("kpiCAC").value),
    ltv: parseFloat(document.getElementById("kpiLTV").value),
    notes: document.getElementById("kpiNotes").value
  };

  const res = await apiCall(`/api/startups/${CURRENT_STARTUP_ID}/kpis`, "POST", payload);
  if (res && res.status === "kpi_recorded") {
    closeLogKPIModal();
    loadMilestones(CURRENT_STARTUP_ID);
    loadPortfolioAnalytics();
  }
}

// Mentorship & Reviews
async function loadMentorshipReviews() {
  const res = await apiCall("/api/mentorship-all");
  const tbody = document.getElementById("mentorshipTableBody");
  tbody.innerHTML = "";

  if (!res || !res.sessions) return;
  res.sessions.forEach(s => {
    const tr = document.createElement("tr");
    const stars = "⭐".repeat(s.health_rating);
    tr.innerHTML = `
      <td>${s.session_date}</td>
      <td><b>${s.startup_name}</b></td>
      <td>${s.mentor_name}</td>
      <td><span class="badge badge-blue">${s.focus_area}</span></td>
      <td>${stars}</td>
      <td>${s.feedback}</td>
      <td><b>${s.action_items || 'None'}</b></td>
    `;
    tbody.appendChild(tr);
  });
}

function openLogMentorshipModal() {
  const sel = document.getElementById("mentorStartupSelect");
  if (sel) sel.value = CURRENT_STARTUP_ID;
  document.getElementById("mentorshipModal").classList.add("active");
}
function closeLogMentorshipModal() { document.getElementById("mentorshipModal").classList.remove("active"); }

async function handleSaveMentorship(e) {
  e.preventDefault();
  const payload = {
    startup_id: parseInt(document.getElementById("mentorStartupSelect").value),
    mentor_name: document.getElementById("mentorName").value,
    focus_area: document.getElementById("mentorFocus").value,
    health_rating: parseInt(document.getElementById("mentorRating").value),
    feedback: document.getElementById("mentorFeedback").value,
    action_items: document.getElementById("mentorActions").value
  };

  const res = await apiCall("/api/mentorship", "POST", payload);
  if (res && res.status === "mentorship_recorded") {
    closeLogMentorshipModal();
    loadMentorshipReviews();
    loadPortfolioAnalytics();
  }
}

// Admin & Scale-up: Add New Startup
async function handleOnboardStartup(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("newStartupName").value,
    tagline: document.getElementById("newStartupTagline").value,
    department: document.getElementById("newStartupDept").value,
    founder_name: document.getElementById("newStartupFounder").value,
    founder_email: document.getElementById("newStartupEmail").value,
    stage: document.getElementById("newStartupStage").value,
    current_phase: parseInt(document.getElementById("newStartupPhase").value),
    team_size: parseInt(document.getElementById("newStartupTeamSize").value)
  };

  const res = await apiCall("/api/startups", "POST", payload);
  if (res && res.status === "success") {
    alert(`Startup '${payload.name}' successfully onboarded! WorkOS Digital Twin and Phase 1-5 Milestones provisioned.`);
    document.getElementById("onboardStartupForm").reset();
    await loadInitialData();
    switchTab("tab-portfolio");
  } else {
    alert("Failed to onboard startup: " + (res ? res.error : "Access denied. Ensure you are logged in as Faculty Incharge."));
  }
}
