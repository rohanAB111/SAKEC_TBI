"""
SAKEC Technology Business Incubator (TBI) Platform — Render + OneDrive Edition
Features:
- Login-gated privacy (safe public showcase; sensitive intern PRN/phone/docs require authentication)
- Admin & User Account Management (create Admin, Authority, Mentor, Founder accounts)
- Auto-create Founder login + 8-item Required Documents Checklist on new startup/pre-incubation onboarding
- OneDrive Integration (linked to incubation@sakec.ac.in master upload link + per-startup folders)
- Official Year-Wise Detailed Reports (2024-25, 2025-26, 2026-27, All Years) — Printable PDF/HTML + CSVs
- Full JSON Backup & Restore for Render Free Tier safety
Developed by Dr. Rohan Appasaheb Borgalli
"""

import http.server
import json
import urllib.parse
import os
import sys
import secrets
import mimetypes
import csv
import io
import html as html_lib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database
from simulator import run_usim_simulation

SESSIONS = {}
PORT = int(os.environ.get("PORT", 8080))


def resolve_static_dir():
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")),
        os.path.abspath(os.path.join(os.getcwd(), "static")),
        os.path.abspath(os.path.join(os.getcwd(), "sakec_tbi_platform", "static")),
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "index.html")):
            return c
    return candidates[0]


STATIC_DIR = resolve_static_dir()


def parse_startup_row(row):
    d = dict(row)
    try:
        d["directors"] = json.loads(d.get("directors_json") or "[]")
    except Exception:
        d["directors"] = []
    return d


def esc(val):
    return html_lib.escape(str(val or ""))


class SAKECTBIRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        payload = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def _get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return SESSIONS.get(auth_header[7:].strip())
        # Also allow ?token=... for direct browser report downloads
        parsed = urllib.parse.urlparse(self.path)
        q_tok = urllib.parse.parse_qs(parsed.query).get("token", [None])[0]
        if q_tok:
            return SESSIONS.get(q_tok)
        return None

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            try:
                return json.loads(self.rfile.read(content_length).decode("utf-8"))
            except Exception:
                return {}
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _serve_static(self, path):
        rel_file = "index.html" if path in ["/", ""] else path.lstrip("/")
        if ".." in rel_file:
            self.send_error(403, "Forbidden")
            return
        candidate_paths = [
            os.path.join(STATIC_DIR, rel_file),
            os.path.join(os.getcwd(), "static", rel_file),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", rel_file),
        ]
        target_path = next((cp for cp in candidate_paths if os.path.exists(cp) and os.path.isfile(cp)), None)
        if not target_path:
            self.send_error(404, f"File not found: {rel_file}")
            return
        ctype, _ = mimetypes.guess_type(target_path)
        if not ctype:
            ctype = "application/javascript" if target_path.endswith(".js") else ("text/css" if target_path.endswith(".css") else "text/html")
        with open(target_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8" if ("text" in ctype or "javascript" in ctype) else ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _generate_official_year_report_html(self, year_filter):
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {r["key"]: r["value"] for r in cursor.fetchall()}

        cursor.execute("SELECT * FROM startups ORDER BY academic_year ASC, incubation_type ASC, id ASC")
        all_startups = [parse_startup_row(r) for r in cursor.fetchall()]
        startups = [
            s for s in all_startups
            if year_filter == "all" or year_filter in [y.strip() for y in (s.get("active_years") or "").split(",")]
        ]
        pvt_list = [s for s in startups if s["incubation_type"] == "Incubated (Pvt. Ltd.)"]
        pre_list = [s for s in startups if s["incubation_type"] != "Incubated (Pvt. Ltd.)"]

        if year_filter != "all":
            cursor.execute("""
                SELECT i.*, s.name AS startup_name, s.incubation_type
                FROM interns i JOIN startups s ON i.startup_id = s.id
                WHERE i.academic_year = ?
                ORDER BY i.semester ASC, s.name ASC, CASE WHEN i.role='Founder' THEN 0 ELSE 1 END
            """, (year_filter,))
        else:
            cursor.execute("""
                SELECT i.*, s.name AS startup_name, s.incubation_type
                FROM interns i JOIN startups s ON i.startup_id = s.id
                ORDER BY i.academic_year DESC, i.semester ASC, s.name ASC, CASE WHEN i.role='Founder' THEN 0 ELSE 1 END
            """)
        interns = [dict(r) for r in cursor.fetchall()]

        startup_ids = [s["id"] for s in startups]
        docs = []
        if startup_ids:
            q_marks = ",".join("?" for _ in startup_ids)
            cursor.execute(f"""
                SELECT d.*, s.name AS startup_name
                FROM documents d JOIN startups s ON d.startup_id = s.id
                WHERE d.startup_id IN ({q_marks})
                ORDER BY s.name ASC, d.id ASC
            """, startup_ids)
            docs = [dict(r) for r in cursor.fetchall()]
        conn.close()

        yr_title = "All Academic Years (2024-25, 2025-26, 2026-27)" if year_filter == "all" else f"Academic Year {year_filter}"
        gen_date = datetime.now().strftime("%d %B %Y, %I:%M %p")

        pvt_rows = ""
        for idx, s in enumerate(pvt_list, 1):
            dirs_html = "<br>".join(f"{esc(d.get('name'))} (DIN: <b>{esc(d.get('din'))}</b>)" for d in s.get("directors", [])) or esc(s["founder_name"])
            pvt_rows += f"""
            <tr>
              <td>{idx}</td>
              <td><b>{esc(s['name'])}</b><br><small>{esc(s['tagline'])}</small></td>
              <td style="font-family:monospace;">{esc(s['cin'])}<br><small>Inc: {esc(s['incorporation_date'])} | {esc(s['roc'])}</small></td>
              <td>{dirs_html}</td>
              <td>{esc(s['department'])}<br><small>Years: {esc(s['active_years'])}</small></td>
              <td>{esc(s['stage'])}<br><small>Phase {s['current_phase']} | Health: {s['health_score']}/100</small></td>
              <td><small>{esc(s['registered_address'])}</small></td>
            </tr>"""

        pre_rows = ""
        for idx, s in enumerate(pre_list, 1):
            pre_rows += f"""
            <tr>
              <td>{idx}</td>
              <td><b>{esc(s['name'])}</b>{f' <small>(formerly {esc(s["former_names"])})</small>' if s.get('former_names') else ''}<br><small>{esc(s['tagline'])}</small></td>
              <td>{esc(s['founder_name'])}<br><small>{esc(s['founder_email'])}</small></td>
              <td>{esc(s['department'])}</td>
              <td>{esc(s['active_years'])}</td>
              <td>{esc(s['stage'])}<br><small>Phase {s['current_phase']} | Health: {s['health_score']}/100</small></td>
            </tr>"""

        intern_rows = ""
        for idx, i in enumerate(interns, 1):
            intern_rows += f"""
            <tr>
              <td>{idx}</td>
              <td>{esc(i['academic_year'])} ({esc(i['semester'])})</td>
              <td><b>{esc(i['startup_name'])}</b></td>
              <td>{esc(i['name'])}</td>
              <td>{esc(i['role'])}</td>
              <td>{esc(i['student_class'])} / {esc(i['department'])}</td>
              <td style="font-family:monospace;">{esc(i['prn'])}</td>
              <td><small>{esc(i['email'])}<br>{esc(i['phone'])}</small></td>
              <td><small>{esc(i['start_date'])} to {esc(i['end_date'])}</small></td>
            </tr>"""

        doc_rows = ""
        for d in docs:
            link = f'<a href="{esc(d["onedrive_url"])}" target="_blank">Open OneDrive / File</a>' if d["onedrive_url"] else "Pending Upload"
            doc_rows += f"""
            <tr>
              <td><b>{esc(d['startup_name'])}</b></td>
              <td>{esc(d['doc_type'])}</td>
              <td>{esc(d['status'])}</td>
              <td>{link}</td>
              <td><small>{esc(d['admin_remarks'])}</small></td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SAKEC TBI Official Report — {esc(yr_title)}</title>
  <style>
    body {{ font-family: "Segoe UI", Arial, sans-serif; color: #111827; margin: 24px; line-height: 1.45; }}
    .no-print {{ background: #0d2a4a; color: #fff; padding: 12px 18px; border-radius: 6px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; }}
    .no-print button {{ background: #d4af37; color: #07192d; border: none; padding: 8px 16px; font-weight: 700; border-radius: 5px; cursor: pointer; }}
    .header {{ text-align: center; border-bottom: 3px solid #0d2a4a; padding-bottom: 12px; margin-bottom: 18px; }}
    .header h1 {{ color: #0d2a4a; margin: 0; font-size: 20px; }}
    .header h2 {{ color: #92400e; margin: 4px 0; font-size: 16px; }}
    .header p {{ margin: 2px 0; font-size: 12px; color: #4b5563; }}
    .kpi-row {{ display: flex; gap: 12px; margin-bottom: 18px; }}
    .kpi {{ flex: 1; border: 1px solid #d1d5db; border-top: 3px solid #0d2a4a; padding: 10px; text-align: center; border-radius: 4px; }}
    .kpi b {{ font-size: 22px; color: #0d2a4a; display: block; }}
    .kpi span {{ font-size: 11px; text-transform: uppercase; color: #4b5563; }}
    h3 {{ color: #0d2a4a; border-left: 4px solid #d4af37; padding-left: 8px; margin-top: 22px; font-size: 15px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin-top: 8px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; color: #0d2a4a; }}
    .sig-row {{ display: flex; justify-content: space-between; margin-top: 48px; padding-top: 12px; }}
    .sig-box {{ text-align: center; width: 240px; border-top: 1px solid #374151; padding-top: 6px; font-size: 12px; }}
    @media print {{ .no-print {{ display: none; }} body {{ margin: 10px; }} }}
  </style>
</head>
<body>
  <div class="no-print">
    <span><b>SAKEC TBI Official Year-Wise Institutional Report</b> ({esc(yr_title)})</span>
    <button onclick="window.print()">🖨️ Print / Save as PDF</button>
  </div>

  <div class="header">
    <h1>SHAH &amp; ANCHOR KUTCHHI ENGINEERING COLLEGE (SAKEC), MUMBAI</h1>
    <h2>Technology Business Incubator (SAKEC TBI) — Annual Progress &amp; Incubation Report</h2>
    <p>{esc(yr_title)} | Generated on: {esc(gen_date)} | OneDrive Repository: {esc(settings.get('onedrive_account', 'incubation@sakec.ac.in'))}</p>
    <p><i>Platform Developed by Dr. Rohan Appasaheb Borgalli</i></p>
  </div>

  <div class="kpi-row">
    <div class="kpi"><b>{len(startups)}</b><span>Total Ventures</span></div>
    <div class="kpi"><b>{len(pvt_list)}</b><span>Incubated (Pvt. Ltd.)</span></div>
    <div class="kpi"><b>{len(pre_list)}</b><span>Pre-Incubation</span></div>
    <div class="kpi"><b>{len(set(i['name'] for i in interns))}</b><span>Unique Founders &amp; Interns</span></div>
    <div class="kpi"><b>{sum(1 for d in docs if d['status'] in ('Submitted','Verified'))}/{len(docs)}</b><span>Docs Submitted / Verified</span></div>
  </div>

  <h3>Section A: Incubated Startups — Private Limited Companies (MCA Verified CIN &amp; DIN)</h3>
  <table>
    <thead><tr><th>#</th><th>Company &amp; Innovation</th><th>CIN &amp; Incorporation</th><th>Directors &amp; DIN</th><th>Department &amp; Years</th><th>Status &amp; Phase</th><th>Registered Office</th></tr></thead>
    <tbody>{pvt_rows or '<tr><td colspan="7">No Pvt. Ltd. startups in this selection.</td></tr>'}</tbody>
  </table>

  <h3>Section B: Pre-Incubation Startups — Non-Pvt. Ltd. Student &amp; Early Ventures</h3>
  <table>
    <thead><tr><th>#</th><th>Venture &amp; Innovation</th><th>Founder(s) &amp; Contact</th><th>Department</th><th>Active Year(s)</th><th>Status &amp; Phase</th></tr></thead>
    <tbody>{pre_rows or '<tr><td colspan="6">No Pre-Incubation ventures in this selection.</td></tr>'}</tbody>
  </table>

  <h3>Section C: Founders &amp; Student Interns Roster ({esc(yr_title)})</h3>
  <table>
    <thead><tr><th>#</th><th>Year &amp; Sem</th><th>Startup</th><th>Student / Founder Name</th><th>Role</th><th>Class / Dept</th><th>PRN</th><th>Contact</th><th>Duration</th></tr></thead>
    <tbody>{intern_rows or '<tr><td colspan="9">No intern records for this selection.</td></tr>'}</tbody>
  </table>

  <h3>Section D: Document Compliance &amp; OneDrive Repository ({esc(settings.get('onedrive_account', 'incubation@sakec.ac.in'))})</h3>
  <table>
    <thead><tr><th>Startup</th><th>Required Document</th><th>Status</th><th>OneDrive / Reference Link</th><th>Remarks</th></tr></thead>
    <tbody>{doc_rows or '<tr><td colspan="5">No document records.</td></tr>'}</tbody>
  </table>

  <div class="sig-row">
    <div class="sig-box"><b>{esc(settings.get('faculty_incharge', 'Dr. Rohan Appasaheb Borgalli'))}</b><br>Faculty Incharge, SAKEC TBI</div>
    <div class="sig-box"><b>{esc(settings.get('principal_name', 'Dr. Bhavesh Patel'))}</b><br>Principal, SAKEC Mumbai</div>
  </div>
</body>
</html>"""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            return self._serve_static(path)

        user = self._get_auth_user()
        year_filter = query.get("year", ["all"])[0]
        type_filter = query.get("type", ["all"])[0]

        # Public safe overview (no student phone numbers, PRNs, or private docs)
        if path == "/api/public/overview":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, tagline, department, academic_year, active_years, incubation_type, cin, stage, current_phase FROM startups ORDER BY academic_year DESC, id ASC")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({
                "total": len(rows),
                "pvt_ltd": sum(1 for r in rows if r["incubation_type"] == "Incubated (Pvt. Ltd.)"),
                "pre_incubation": sum(1 for r in rows if r["incubation_type"] != "Incubated (Pvt. Ltd.)"),
                "startups": rows
            })

        # All remaining API endpoints require authentication (Login-gated for public Render deployment!)
        if path == "/api/me":
            if not user:
                return self._send_json({"error": "Unauthorized"}, 401)
            return self._send_json({"user": user})

        if not user:
            return self._send_json({"error": "Authentication required. Please log in."}, 401)

        if path == "/api/settings":
            conn = database.get_db()
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            conn.close()
            return self._send_json({"settings": {r["key"]: r["value"] for r in rows}})

        elif path == "/api/users":
            if user.get("role") not in ["faculty_incharge", "authority"]:
                return self._send_json({"error": "Admin access required"}, 403)
            conn = database.get_db()
            rows = conn.execute("""
                SELECT u.id, u.username, u.full_name, u.email, u.role, u.startup_id, u.designation, u.active, u.created_at, s.name AS startup_name
                FROM users u LEFT JOIN startups s ON u.startup_id = s.id
                ORDER BY CASE u.role WHEN 'faculty_incharge' THEN 1 WHEN 'authority' THEN 2 WHEN 'mentor' THEN 3 ELSE 4 END, u.id ASC
            """).fetchall()
            conn.close()
            return self._send_json({"users": [dict(r) for r in rows]})

        elif path == "/api/startups":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM startups ORDER BY academic_year DESC, incubation_type ASC, id ASC")
            rows = [parse_startup_row(r) for r in cursor.fetchall()]
            filtered = []
            for s in rows:
                years = [y.strip() for y in (s.get("active_years") or s.get("academic_year") or "").split(",") if y.strip()]
                if year_filter != "all" and year_filter not in years:
                    continue
                if type_filter != "all" and s.get("incubation_type") != type_filter:
                    continue
                if year_filter != "all":
                    cursor.execute("SELECT COUNT(DISTINCT name) FROM interns WHERE startup_id = ? AND academic_year = ?", (s["id"], year_filter))
                else:
                    cursor.execute("SELECT COUNT(DISTINCT name) FROM interns WHERE startup_id = ?", (s["id"],))
                s["intern_count"] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM documents WHERE startup_id = ? AND status IN ('Submitted','Verified')", (s["id"],))
                s["docs_submitted"] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM documents WHERE startup_id = ?", (s["id"],))
                s["docs_total"] = cursor.fetchone()[0]
                filtered.append(s)
            conn.close()
            return self._send_json({"startups": filtered})

        elif path == "/api/documents":
            startup_id = query.get("startup_id", ["all"])[0]
            conn = database.get_db()
            cursor = conn.cursor()
            sql = """
                SELECT d.*, s.name AS startup_name, s.incubation_type, s.onedrive_folder_url
                FROM documents d JOIN startups s ON d.startup_id = s.id
                WHERE 1=1
            """
            params = []
            if user.get("role") == "founder" and user.get("startup_id"):
                sql += " AND d.startup_id = ?"
                params.append(user["startup_id"])
            elif startup_id != "all":
                sql += " AND d.startup_id = ?"
                params.append(int(startup_id))
            if year_filter != "all":
                sql += " AND (d.academic_year = ? OR s.active_years LIKE ?)"
                params.extend([year_filter, f"%{year_filter}%"])
            sql += " ORDER BY s.name ASC, d.id ASC"
            rows = [dict(r) for r in cursor.execute(sql, params).fetchall()]
            conn.close()
            return self._send_json({"documents": rows})

        elif path == "/api/interns":
            startup_id = query.get("startup_id", ["all"])[0]
            semester = query.get("semester", ["all"])[0]
            conn = database.get_db()
            cursor = conn.cursor()
            sql = "SELECT i.*, s.name AS startup_name, s.incubation_type, s.cin FROM interns i JOIN startups s ON i.startup_id = s.id WHERE 1=1"
            params = []
            if user.get("role") == "founder" and user.get("startup_id"):
                sql += " AND i.startup_id = ?"
                params.append(user["startup_id"])
            elif startup_id != "all":
                sql += " AND i.startup_id = ?"
                params.append(int(startup_id))
            if year_filter != "all":
                sql += " AND i.academic_year = ?"
                params.append(year_filter)
            if semester != "all":
                sql += " AND i.semester = ?"
                params.append(semester)
            sql += " ORDER BY i.academic_year DESC, i.semester ASC, s.name ASC, CASE WHEN i.role='Founder' THEN 0 ELSE 1 END, i.id ASC"
            rows = [dict(r) for r in cursor.execute(sql, params).fetchall()]
            conn.close()
            return self._send_json({"interns": rows})

        elif path.startswith("/api/startups/") and path.endswith("/digital-twin"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            twin = conn.execute("SELECT * FROM digital_twins WHERE startup_id = ?", (startup_id,)).fetchone()
            conn.close()
            if twin:
                t_dict = dict(twin)
                for key in ("business_model", "product_roadmap", "team_structure"):
                    try:
                        t_dict[key] = json.loads(t_dict[key])
                    except Exception:
                        pass
                return self._send_json({"digital_twin": t_dict})
            return self._send_json({"digital_twin": None})

        elif path.startswith("/api/startups/") and path.endswith("/milestones"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            rows = [dict(r) for r in conn.execute("SELECT * FROM milestones WHERE startup_id = ? ORDER BY phase ASC, target_date ASC", (startup_id,)).fetchall()]
            conn.close()
            return self._send_json({"milestones": rows})

        elif path.startswith("/api/startups/") and path.endswith("/kpis"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            rows = [dict(r) for r in conn.execute("SELECT * FROM kpi_records WHERE startup_id = ? ORDER BY month ASC", (startup_id,)).fetchall()]
            conn.close()
            return self._send_json({"kpis": rows})

        elif path.startswith("/api/startups/") and path.endswith("/simulations"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            rows = [dict(r) for r in conn.execute("SELECT * FROM simulations WHERE startup_id = ? ORDER BY id DESC", (startup_id,)).fetchall()]
            conn.close()
            return self._send_json({"simulations": rows})

        elif path.startswith("/api/startups/") and len(path.split("/")) == 4:
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            st = conn.execute("SELECT * FROM startups WHERE id = ?", (startup_id,)).fetchone()
            conn.close()
            return self._send_json({"startup": parse_startup_row(st)}) if st else self._send_json({"error": "Not found"}, 404)

        elif path == "/api/mentorship-all":
            conn = database.get_db()
            rows = [dict(r) for r in conn.execute("SELECT m.*, s.name as startup_name FROM mentorship_sessions m JOIN startups s ON m.startup_id = s.id ORDER BY m.session_date DESC").fetchall()]
            conn.close()
            return self._send_json({"sessions": rows})

        elif path == "/api/analytics/portfolio":
            conn = database.get_db()
            cursor = conn.cursor()
            all_startups = [parse_startup_row(r) for r in cursor.execute("SELECT * FROM startups").fetchall()]
            startups = [s for s in all_startups if year_filter == "all" or year_filter in [y.strip() for y in (s.get("active_years") or "").split(",")]]

            total_startups = len(startups)
            pvt_ltd_count = sum(1 for s in startups if s["incubation_type"] == "Incubated (Pvt. Ltd.)")
            pre_inc_count = total_startups - pvt_ltd_count
            avg_health = round(sum(s["health_score"] for s in startups) / total_startups, 1) if total_startups else 0

            phase_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for s in startups:
                phase_counts[s["current_phase"]] = phase_counts.get(s["current_phase"], 0) + 1

            year_summary = {}
            for yr in ("2024-25", "2025-26", "2026-27"):
                yr_st = [s for s in all_startups if yr in [y.strip() for y in (s.get("active_years") or "").split(",")]]
                yr_interns = cursor.execute("SELECT COUNT(DISTINCT name) FROM interns WHERE academic_year = ?", (yr,)).fetchone()[0]
                year_summary[yr] = {
                    "total": len(yr_st),
                    "pvt_ltd": sum(1 for s in yr_st if s["incubation_type"] == "Incubated (Pvt. Ltd.)"),
                    "pre_incubation": sum(1 for s in yr_st if s["incubation_type"] != "Incubated (Pvt. Ltd.)"),
                    "students_engaged": yr_interns
                }

            total_students_engaged = cursor.execute("SELECT COUNT(DISTINCT name) FROM interns WHERE academic_year = ?", (year_filter,)).fetchone()[0] if year_filter != "all" else cursor.execute("SELECT COUNT(DISTINCT name) FROM interns").fetchone()[0]
            docs_submitted = cursor.execute("SELECT COUNT(*) FROM documents WHERE status IN ('Submitted','Verified')").fetchone()[0]
            docs_total = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            conn.close()

            return self._send_json({
                "summary": {
                    "total_startups": total_startups,
                    "pvt_ltd_count": pvt_ltd_count,
                    "pre_incubation_count": pre_inc_count,
                    "avg_health_score": avg_health,
                    "total_students_engaged": total_students_engaged,
                    "docs_submitted": docs_submitted,
                    "docs_total": docs_total,
                    "phase_distribution": phase_counts,
                    "year_summary": year_summary
                }
            })

        elif path == "/api/export/detailed-report":
            report_html = self._generate_official_year_report_html(year_filter).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(report_html)))
            self.end_headers()
            self.wfile.write(report_html)
            return

        elif path == "/api/export/csv":
            conn = database.get_db()
            rows = [parse_startup_row(r) for r in conn.execute("SELECT * FROM startups ORDER BY academic_year ASC, id ASC").fetchall()]
            conn.close()
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["ID", "Startup Name", "Academic Year", "Active Years", "Track", "CIN", "Incorporation Date", "ROC", "Authorized Capital", "Paid-up Capital", "Directors & DIN", "Founder(s)", "Department", "Phase", "Stage", "Health Score", "OneDrive Folder", "Registered Address"])
            for s in rows:
                if year_filter != "all" and year_filter not in [y.strip() for y in (s.get("active_years") or "").split(",")]:
                    continue
                dirs_str = "; ".join(f"{d.get('name')} (DIN: {d.get('din')})" for d in s.get("directors", []))
                w.writerow([s["id"], s["name"], s["academic_year"], s["active_years"], s["incubation_type"], s["cin"], s["incorporation_date"], s["roc"], s["authorized_capital"], s["paid_up_capital"], dirs_str, s["founder_name"], s["department"], f"Phase {s['current_phase']}", s["stage"], s["health_score"], s["onedrive_folder_url"], s["registered_address"]])
            data = buf.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="sakec_tbi_startups_{year_filter}.csv"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/export/interns-csv":
            conn = database.get_db()
            sql = "SELECT i.academic_year, i.semester, s.name, s.incubation_type, i.name, i.role, i.student_class, i.department, i.prn, i.phone, i.email, i.timings, i.start_date, i.end_date FROM interns i JOIN startups s ON i.startup_id = s.id"
            params = [year_filter] if year_filter != "all" else []
            if year_filter != "all":
                sql += " WHERE i.academic_year = ?"
            sql += " ORDER BY i.academic_year DESC, i.semester ASC, s.name ASC"
            rows = conn.execute(sql, params).fetchall()
            conn.close()
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["Academic Year", "Semester", "Startup", "Track", "Name", "Role", "Class", "Department", "PRN", "Phone", "Email", "Timings", "Start Date", "End Date"])
            for r in rows:
                w.writerow(list(r))
            data = buf.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="sakec_tbi_interns_{year_filter}.csv"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/admin/backup-json":
            if user.get("role") != "faculty_incharge":
                return self._send_json({"error": "Admin only"}, 403)
            conn = database.get_db()
            dump = {}
            for tbl in ("settings", "startups", "documents", "interns", "digital_twins", "milestones", "kpi_records", "simulations", "mentorship_sessions"):
                dump[tbl] = [dict(r) for r in conn.execute(f"SELECT * FROM {tbl}").fetchall()]
            conn.close()
            data = json.dumps(dump, indent=2, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="sakec_tbi_backup_{datetime.now().strftime("%Y%m%d")}.json"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        return self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()
        user = self._get_auth_user()

        if path == "/api/login":
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            conn = database.get_db()
            row = conn.execute("SELECT * FROM users WHERE username = ? AND password_hash = ? AND active = 1", (username, database.hash_password(password))).fetchone()
            conn.close()
            if row:
                u_dict = dict(row)
                del u_dict["password_hash"]
                token = secrets.token_hex(24)
                SESSIONS[token] = u_dict
                return self._send_json({"token": token, "user": u_dict})
            return self._send_json({"error": "Invalid username or password"}, 401)

        elif path == "/api/logout":
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                SESSIONS.pop(auth_header[7:].strip(), None)
            return self._send_json({"status": "logged_out"})

        if not user:
            return self._send_json({"error": "Authentication required"}, 401)

        if path == "/api/change-password":
            old_p = body.get("old_password", "")
            new_p = body.get("new_password", "").strip()
            if len(new_p) < 6:
                return self._send_json({"error": "New password must be at least 6 characters"}, 400)
            conn = database.get_db()
            row = conn.execute("SELECT id FROM users WHERE id = ? AND password_hash = ?", (user["id"], database.hash_password(old_p))).fetchone()
            if not row:
                conn.close()
                return self._send_json({"error": "Current password is incorrect"}, 400)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (database.hash_password(new_p), user["id"]))
            conn.commit()
            conn.close()
            return self._send_json({"status": "password_changed"})

        elif path == "/api/users":
            if user.get("role") != "faculty_incharge":
                return self._send_json({"error": "Only Faculty Incharge / Admin can create user accounts"}, 403)
            uname = body.get("username", "").strip()
            pwd = body.get("password", "").strip() or "Sakec@123"
            full_name = body.get("full_name", "").strip()
            email = body.get("email", "").strip()
            role = body.get("role", "faculty_incharge").strip()
            startup_id = int(body["startup_id"]) if body.get("startup_id") else None
            designation = body.get("designation", "").strip()
            if not uname or not full_name:
                return self._send_json({"error": "Username and Full Name are required"}, 400)
            conn = database.get_db()
            try:
                conn.execute("""
                INSERT INTO users (username, password_hash, full_name, email, role, startup_id, designation, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (uname, database.hash_password(pwd), full_name, email, role, startup_id, designation, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                return self._send_json({"status": "user_created", "username": uname})
            except Exception as e:
                conn.close()
                return self._send_json({"error": str(e)}, 400)

        elif path == "/api/settings":
            if user.get("role") != "faculty_incharge":
                return self._send_json({"error": "Admin access required"}, 403)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            for k, v in body.items():
                conn.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)", (str(k), str(v), now))
            conn.commit()
            conn.close()
            return self._send_json({"status": "settings_saved"})

        elif path == "/api/startups":
            if user.get("role") not in ["faculty_incharge", "authority"]:
                return self._send_json({"error": "Admin access required"}, 403)
            name = body.get("name", "").strip()
            tagline = body.get("tagline", "").strip()
            department = body.get("department", "SAKEC Engineering").strip()
            academic_year = body.get("academic_year", "2026-27").strip()
            active_years = body.get("active_years", academic_year).strip() or academic_year
            incubation_type = body.get("incubation_type", "Pre-Incubation").strip()
            cin = body.get("cin", "").strip()
            if cin:
                incubation_type = "Incubated (Pvt. Ltd.)"
            incorporation_date = body.get("incorporation_date", "").strip()
            roc = body.get("roc", "RoC-Mumbai" if cin else "").strip()
            registered_address = body.get("registered_address", "").strip()
            directors_json = json.dumps(body.get("directors", [])) if isinstance(body.get("directors"), list) else (body.get("directors_json") or "[]")
            founder_name = body.get("founder_name", "").strip()
            founder_email = body.get("founder_email", "").strip()
            founder_phone = body.get("founder_phone", "").strip()
            website_url = body.get("website_url", "").strip()
            onedrive_folder_url = body.get("onedrive_folder_url", "").strip()
            stage = body.get("stage", "Prototype / Proof of Concept").strip()
            current_phase = int(body.get("current_phase", 1))
            team_size = int(body.get("team_size", 2))
            founder_username = body.get("founder_username", "").strip()
            founder_password = body.get("founder_password", "").strip() or "Sakec@123"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not name or not founder_name:
                return self._send_json({"error": "Startup name and founder name are required"}, 400)

            conn = database.get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO startups (
                    name, tagline, department, academic_year, active_years, incubation_type,
                    cin, incorporation_date, roc, registered_address, directors_json,
                    founder_name, founder_email, founder_phone, website_url, onedrive_folder_url,
                    current_phase, health_score, stage, monthly_burn, cash_in_bank, runway_months,
                    monthly_revenue, customer_count, team_size, investor_readiness_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 75, ?, 20000, 200000, 10.0, 0, 0, ?, 68, ?, ?)
                """, (
                    name, tagline, department, academic_year, active_years, incubation_type,
                    cin, incorporation_date, roc, registered_address, directors_json,
                    founder_name, founder_email, founder_phone, website_url, onedrive_folder_url,
                    current_phase, stage, team_size, now, now
                ))
                new_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO digital_twins (startup_id, business_model, target_market, value_proposition, product_roadmap, team_structure, sales_pipeline_stage, risk_assessment, tech_stack, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id, json.dumps({"model": "To be finalized in Phase 2 USim", "pricing": "TBD"}),
                    "Target customer segment", tagline,
                    json.dumps([{"q": academic_year, "item": "Onboarding & MVP Development", "status": "In Progress"}]),
                    json.dumps([{"role": "Founder", "name": founder_name, "dept": department}]),
                    "Onboarding & Discovery", "Execution & compliance risks", "TBD", now
                ))

                cursor.execute("""
                INSERT INTO interns (startup_id, academic_year, semester, name, role, department, email, phone, created_at)
                VALUES (?, ?, 'Odd Sem', ?, 'Founder', ?, ?, ?, ?)
                """, (new_id, academic_year, founder_name, department, founder_email, founder_phone, now))

                # Auto-provision required documents checklist for founder to upload to incubation@sakec.ac.in OneDrive
                database.provision_default_documents(cursor, new_id, academic_year, incubation_type, now)

                # Auto-create Founder Login Account if username provided
                created_username = None
                if founder_username:
                    cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role, startup_id, designation, active, created_at)
                    VALUES (?, ?, ?, ?, 'founder', ?, ?, 1, ?)
                    """, (founder_username, database.hash_password(founder_password), founder_name, founder_email, new_id, f"Founder, {name}", now))
                    created_username = founder_username

                for p_num, title in [
                    (1, "Phase 1: Onboarding, OneDrive Document Submission & Digital Twin"),
                    (2, "Phase 2: USim Unit Economics & Pricing Simulation"),
                    (3, "Phase 3: WorkOS Operational Deployment & Pilot"),
                    (4, "Phase 4: Mentorship Audit & Regulatory Readiness"),
                    (5, "Phase 5: SAKEC Demo Day & Investor Readiness")
                ]:
                    cursor.execute("INSERT INTO milestones (startup_id, title, phase, target_date, status, created_at) VALUES (?, ?, ?, date('now', '+30 day'), ?, ?)", (new_id, title, p_num, "In Progress" if p_num == 1 else "Pending", now))

                conn.commit()
                conn.close()
                return self._send_json({"status": "success", "startup_id": new_id, "founder_username": created_username})
            except Exception as e:
                conn.close()
                return self._send_json({"error": str(e)}, 500)

        elif path == "/api/documents":
            startup_id = int(body.get("startup_id", user.get("startup_id") or 1))
            if user.get("role") == "founder" and user.get("startup_id") != startup_id:
                return self._send_json({"error": "Founders can only upload documents for their own startup"}, 403)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            conn.execute("""
            INSERT INTO documents (startup_id, academic_year, doc_type, title, onedrive_url, status, uploaded_by, admin_remarks, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                startup_id, body.get("academic_year", "2026-27"),
                body.get("doc_type", "Additional Document"),
                body.get("title", "Uploaded Document"),
                body.get("onedrive_url", "").strip(),
                "Submitted" if body.get("onedrive_url", "").strip() else "Pending",
                user.get("full_name", ""),
                body.get("admin_remarks", ""),
                now
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "document_added"})

        elif path == "/api/interns":
            startup_id = int(body.get("startup_id", user.get("startup_id") or 1))
            if user.get("role") == "founder" and user.get("startup_id") != startup_id:
                return self._send_json({"error": "Founders can only add interns to their own startup"}, 403)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            conn.execute("""
            INSERT INTO interns (startup_id, academic_year, semester, name, role, student_class, department, prn, phone, email, timings, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                startup_id, body.get("academic_year", "2026-27"), body.get("semester", "Odd Sem"),
                body.get("name", "").strip(), body.get("role", "Intern"), body.get("student_class", ""),
                body.get("department", ""), body.get("prn", ""), body.get("phone", ""), body.get("email", ""),
                body.get("timings", "10 am - 5 pm"), body.get("start_date", ""), body.get("end_date", ""), now
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "intern_added"})

        elif path.startswith("/api/startups/") and path.endswith("/simulate"):
            return self._send_json(run_usim_simulation(
                float(body.get("base_price", 1000.0)), float(body.get("monthly_fixed_cost", 50000.0)),
                float(body.get("variable_cost_per_unit", 100.0)), float(body.get("marketing_spend", 10000.0)),
                float(body.get("organic_growth_rate", 10.0)), float(body.get("churn_rate", 3.0)),
                float(body.get("initial_cash", 500000.0)), int(body.get("initial_customers", 5)), float(body.get("cac", 2000.0))
            ))

        elif path.startswith("/api/startups/") and path.endswith("/save-simulation"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            conn.execute("""
            INSERT INTO simulations (startup_id, scenario_name, base_price, monthly_fixed_cost, variable_cost_per_unit, marketing_spend, organic_growth_rate, churn_rate, runway_result_months, break_even_month, projected_arr, simulation_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                startup_id, body.get("scenario_name", "USim Scenario"), float(body.get("base_price", 1000.0)),
                float(body.get("monthly_fixed_cost", 50000.0)), float(body.get("variable_cost_per_unit", 100.0)),
                float(body.get("marketing_spend", 10000.0)), float(body.get("organic_growth_rate", 10.0)),
                float(body.get("churn_rate", 3.0)), float(body.get("runway_months", 12.0)),
                int(body.get("break_even_month", 6)), float(body.get("projected_arr", 1200000.0)),
                datetime.now().strftime("%Y-%m-%d"), body.get("notes", "")
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "simulation_saved"})

        elif path.startswith("/api/startups/") and path.endswith("/kpis"):
            startup_id = int(path.split("/")[3])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rev, burn, cust = float(body.get("revenue", 0.0)), float(body.get("burn_rate", 0.0)), int(body.get("paying_customers", 0))
            conn = database.get_db()
            conn.execute("INSERT INTO kpi_records (startup_id, month, revenue, burn_rate, active_users, paying_customers, cac, ltv, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (startup_id, body.get("month", datetime.now().strftime("%Y-%m")), rev, burn, int(body.get("active_users", 0)), cust, float(body.get("cac", 0.0)), float(body.get("ltv", 0.0)), body.get("notes", ""), now))
            conn.execute("UPDATE startups SET monthly_revenue=?, monthly_burn=?, customer_count=?, updated_at=? WHERE id=?", (rev, burn, cust, now, startup_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "kpi_recorded"})

        elif path.startswith("/api/startups/") and path.endswith("/milestones"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            conn.execute("INSERT INTO milestones (startup_id, title, phase, target_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                         (startup_id, body.get("title", "").strip(), int(body.get("phase", 1)), body.get("target_date", datetime.now().strftime("%Y-%m-%d")), "Pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            return self._send_json({"status": "milestone_created"})

        elif path == "/api/mentorship":
            startup_id = int(body.get("startup_id", 1))
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            conn.execute("INSERT INTO mentorship_sessions (startup_id, mentor_name, mentor_email, session_date, focus_area, feedback, health_rating, action_items, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?)",
                         (startup_id, body.get("mentor_name", user["full_name"]), user["email"], body.get("session_date", datetime.now().strftime("%Y-%m-%d")), body.get("focus_area", "Review"), body.get("feedback", ""), int(body.get("health_rating", 4)), body.get("action_items", ""), now))
            avg_r = conn.execute("SELECT AVG(health_rating) FROM mentorship_sessions WHERE startup_id = ?", (startup_id,)).fetchone()[0] or 4.0
            new_h = min(98, max(50, int(avg_r * 18 + 10)))
            conn.execute("UPDATE startups SET health_score = ?, updated_at = ? WHERE id = ?", (new_h, now, startup_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "mentorship_recorded", "new_health_score": new_h})

        return self._send_json({"error": "Endpoint not found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()
        user = self._get_auth_user()
        if not user:
            return self._send_json({"error": "Authentication required"}, 401)

        if path.startswith("/api/documents/"):
            doc_id = int(path.split("/")[3])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            cur = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
            if not cur:
                conn.close()
                return self._send_json({"error": "Document not found"}, 404)
            if user.get("role") == "founder" and user.get("startup_id") != cur["startup_id"]:
                conn.close()
                return self._send_json({"error": "Forbidden"}, 403)
            new_url = body.get("onedrive_url", cur["onedrive_url"])
            new_status = body.get("status", "Submitted" if new_url else cur["status"])
            if user.get("role") == "founder" and new_status == "Verified":
                new_status = "Submitted"
            conn.execute("""
            UPDATE documents SET onedrive_url = ?, status = ?, uploaded_by = ?, admin_remarks = ?, updated_at = ? WHERE id = ?
            """, (new_url, new_status, user.get("full_name", cur["uploaded_by"]), body.get("admin_remarks", cur["admin_remarks"]), now, doc_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "document_updated"})

        elif path.startswith("/api/users/"):
            if user.get("role") != "faculty_incharge":
                return self._send_json({"error": "Admin only"}, 403)
            uid = int(path.split("/")[3])
            conn = database.get_db()
            if body.get("new_password"):
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (database.hash_password(body["new_password"]), uid))
            if "active" in body:
                conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if body["active"] else 0, uid))
            conn.commit()
            conn.close()
            return self._send_json({"status": "user_updated"})

        elif path.startswith("/api/startups/") and path.endswith("/digital-twin"):
            startup_id = int(path.split("/")[3])
            if user.get("role") == "founder" and user.get("startup_id") != startup_id:
                return self._send_json({"error": "Forbidden"}, 403)
            conn = database.get_db()
            conn.execute("""
            UPDATE digital_twins SET target_market=COALESCE(?,target_market), value_proposition=COALESCE(?,value_proposition),
            sales_pipeline_stage=COALESCE(?,sales_pipeline_stage), risk_assessment=COALESCE(?,risk_assessment),
            tech_stack=COALESCE(?,tech_stack), updated_at=? WHERE startup_id=?
            """, (body.get("target_market"), body.get("value_proposition"), body.get("sales_pipeline_stage"), body.get("risk_assessment"), body.get("tech_stack"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), startup_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "digital_twin_updated"})

        elif path.startswith("/api/startups/") and len(path.split("/")) == 4:
            startup_id = int(path.split("/")[3])
            if user.get("role") == "founder" and user.get("startup_id") != startup_id:
                return self._send_json({"error": "Forbidden"}, 403)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = database.get_db()
            cur = conn.execute("SELECT * FROM startups WHERE id = ?", (startup_id,)).fetchone()
            if not cur:
                conn.close()
                return self._send_json({"error": "Not found"}, 404)
            burn = float(body.get("monthly_burn", cur["monthly_burn"]))
            cash = float(body.get("cash_in_bank", cur["cash_in_bank"]))
            rev = float(body.get("monthly_revenue", cur["monthly_revenue"]))
            net_burn = max(0, burn - rev)
            runway = round(cash / net_burn, 1) if net_burn > 0 else 99.0
            conn.execute("""
            UPDATE startups SET name=?, tagline=?, department=?, academic_year=?, active_years=?, incubation_type=?,
            cin=?, incorporation_date=?, registered_address=?, onedrive_folder_url=?, founder_name=?, founder_email=?,
            current_phase=?, stage=?, health_score=?, monthly_burn=?, cash_in_bank=?, runway_months=?, monthly_revenue=?, updated_at=?
            WHERE id=?
            """, (
                body.get("name", cur["name"]), body.get("tagline", cur["tagline"]), body.get("department", cur["department"]),
                body.get("academic_year", cur["academic_year"]), body.get("active_years", cur["active_years"]),
                body.get("incubation_type", cur["incubation_type"]), body.get("cin", cur["cin"]),
                body.get("incorporation_date", cur["incorporation_date"]), body.get("registered_address", cur["registered_address"]),
                body.get("onedrive_folder_url", cur["onedrive_folder_url"]), body.get("founder_name", cur["founder_name"]),
                body.get("founder_email", cur["founder_email"]), int(body.get("current_phase", cur["current_phase"])),
                body.get("stage", cur["stage"]), int(body.get("health_score", cur["health_score"])),
                burn, cash, runway, rev, now, startup_id
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "startup_updated", "runway_months": runway})

        elif path.startswith("/api/milestones/"):
            mid = int(path.split("/")[3])
            conn = database.get_db()
            conn.execute("UPDATE milestones SET status=COALESCE(?,status), verification_notes=COALESCE(?,verification_notes), completion_date=COALESCE(?,completion_date) WHERE id=?",
                         (body.get("status"), body.get("verification_notes"), body.get("completion_date"), mid))
            conn.commit()
            conn.close()
            return self._send_json({"status": "milestone_updated"})

        return self._send_json({"error": "Endpoint not found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        user = self._get_auth_user()
        if not user or user.get("role") != "faculty_incharge":
            return self._send_json({"error": "Admin only"}, 403)
        if path.startswith("/api/users/"):
            uid = int(path.split("/")[3])
            if uid == user["id"]:
                return self._send_json({"error": "Cannot delete your own active admin account"}, 400)
            conn = database.get_db()
            conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            conn.commit()
            conn.close()
            return self._send_json({"status": "user_deleted"})
        return self._send_json({"error": "Endpoint not found"}, 404)


def run_server():
    database.init_db()
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), SAKECTBIRequestHandler)
    print("=====================================================================")
    print(" SAKEC TBI Platform (Render + OneDrive + Year-Wise Reports)")
    print(" Developed by Dr. Rohan Appasaheb Borgalli")
    print(f" Running at http://0.0.0.0:{PORT}")
    print("=====================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
