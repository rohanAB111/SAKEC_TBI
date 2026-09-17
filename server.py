"""
SAKEC Technology Business Incubator (TBI) Platform
Core Server Engine - Multi-Threaded HTTP REST API & Static File Server
Developed by Dr. Rohan Appasaheb Borgalli
"""

import http.server
import json
import urllib.parse
import os
import sys
import secrets
import mimetypes
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
import database
# Embedded USim simulation engine
# Simulator
def run_usim_simulation(base_price, monthly_fixed_cost, variable_cost_per_unit, marketing_spend, organic_growth_rate, churn_rate, initial_cash=500000.0, initial_customers=5, cac=2000.0, projection_months=12):
    contribution_margin = base_price - variable_cost_per_unit
    margin_percentage = (contribution_margin / base_price * 100) if base_price > 0 else 0
    effective_cac = max(cac, 100.0)
    monthly_projections = []
    current_customers = initial_customers
    current_cash = initial_cash
    break_even_month = None
    cash_out_month = None

    for m in range(1, projection_months + 1):
        churned = int(current_customers * (churn_rate / 100.0))
        paid_acquisitions = int(marketing_spend / effective_cac) if effective_cac > 0 else 0
        organic_acquisitions = max(1, int(current_customers * (organic_growth_rate / 100.0))) if current_customers > 0 else 1
        new_customers = paid_acquisitions + organic_acquisitions
        current_customers = max(0, current_customers - churned + new_customers)
        
        revenue = current_customers * base_price
        var_costs = current_customers * variable_cost_per_unit
        total_costs = monthly_fixed_cost + var_costs + marketing_spend
        net_flow = revenue - total_costs
        current_cash += net_flow
        
        if revenue >= total_costs and break_even_month is None:
            break_even_month = m
            
        if current_cash <= 0 and cash_out_month is None:
            cash_out_month = m

        monthly_projections.append({
            'month': m,
            'customers': current_customers,
            'revenue': round(revenue, 2),
            'fixed_cost': round(monthly_fixed_cost, 2),
            'variable_cost': round(var_costs, 2),
            'marketing_spend': round(marketing_spend, 2),
            'total_expenses': round(total_costs, 2),
            'net_cash_flow': round(net_flow, 2),
            'cash_balance': round(current_cash, 2)
        })

    latest = monthly_projections[-1]
    projected_arr = latest['revenue'] * 12
    latest_burn = max(0, latest['total_expenses'] - latest['revenue'])
    runway_months = round(current_cash / latest_burn, 1) if latest_burn > 0 else (99.0 if current_cash > 0 else 0.0)
    avg_lifetime_months = (100.0 / churn_rate) if churn_rate > 0 else 36.0
    ltv = contribution_margin * avg_lifetime_months
    ltv_cac_ratio = round(ltv / effective_cac, 2) if effective_cac > 0 else 0

    return {
        'summary': {
            'contribution_margin': round(contribution_margin, 2),
            'margin_percentage': round(margin_percentage, 1),
            'effective_cac': round(effective_cac, 2),
            'estimated_ltv': round(ltv, 2),
            'ltv_cac_ratio': ltv_cac_ratio,
            'break_even_month': break_even_month if break_even_month else 'Beyond 12 Months',
            'cash_out_month': cash_out_month if cash_out_month else 'Sufficient Runway',
            'final_projected_cash': round(current_cash, 2),
            'projected_arr': round(projected_arr, 2),
            'runway_months': runway_months,
            'final_customer_count': current_customers
        },
        'monthly_projections': monthly_projections
    }


# In-memory session store: token -> user_dict
SESSIONS = {}

PORT = int(os.environ.get("PORT", 8080))
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class SAKECTBIRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return SESSIONS.get(token)
        return None

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                return json.loads(body)
            except Exception:
                return {}
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static assets routing
        if not path.startswith("/api/"):
            if path == "/" or path == "":
                self.path = "/index.html"
            return super().do_GET()

        # REST API Routes
        user = self._get_auth_user()

        if path == "/api/me":
            if not user:
                return self._send_json({"error": "Unauthorized"}, 401)
            return self._send_json({"user": user})

        elif path == "/api/startups":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM startups ORDER BY id ASC")
            startups = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return self._send_json({"startups": startups})

        elif path.startswith("/api/startups/") and path.endswith("/digital-twin"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM digital_twins WHERE startup_id = ?", (startup_id,))
            twin = cursor.fetchone()
            conn.close()
            if twin:
                t_dict = dict(twin)
                try:
                    t_dict["business_model"] = json.loads(t_dict["business_model"])
                except Exception:
                    pass
                try:
                    t_dict["product_roadmap"] = json.loads(t_dict["product_roadmap"])
                except Exception:
                    pass
                try:
                    t_dict["team_structure"] = json.loads(t_dict["team_structure"])
                except Exception:
                    pass
                return self._send_json({"digital_twin": t_dict})
            return self._send_json({"digital_twin": None})

        elif path.startswith("/api/startups/") and path.endswith("/milestones"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM milestones WHERE startup_id = ? ORDER BY phase ASC, target_date ASC", (startup_id,))
            milestones = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"milestones": milestones})

        elif path.startswith("/api/startups/") and path.endswith("/kpis"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kpi_records WHERE startup_id = ? ORDER BY month ASC", (startup_id,))
            kpis = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"kpis": kpis})

        elif path.startswith("/api/startups/") and path.endswith("/simulations"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM simulations WHERE startup_id = ? ORDER BY id DESC", (startup_id,))
            sims = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"simulations": sims})

        elif path.startswith("/api/startups/") and path.endswith("/mentorship"):
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mentorship_sessions WHERE startup_id = ? ORDER BY session_date DESC", (startup_id,))
            sessions = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"mentorship_sessions": sessions})

        elif path.startswith("/api/startups/") and len(path.split("/")) == 4:
            startup_id = int(path.split("/")[3])
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM startups WHERE id = ?", (startup_id,))
            st = cursor.fetchone()
            conn.close()
            if st:
                return self._send_json({"startup": dict(st)})
            return self._send_json({"error": "Startup not found"}, 404)

        elif path == "/api/mentorship-all":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, s.name as startup_name 
                FROM mentorship_sessions m 
                JOIN startups s ON m.startup_id = s.id 
                ORDER BY m.session_date DESC
            """)
            sessions = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return self._send_json({"sessions": sessions})

        elif path == "/api/analytics/portfolio":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM startups")
            startups = [dict(r) for r in cursor.fetchall()]
            
            total_startups = len(startups)
            total_revenue = sum(s["monthly_revenue"] for s in startups)
            avg_health = round(sum(s["health_score"] for s in startups) / total_startups, 1) if total_startups else 0
            avg_investor_readiness = round(sum(s["investor_readiness_score"] for s in startups) / total_startups, 1) if total_startups else 0
            total_team_members = sum(s["team_size"] for s in startups)
            total_paying_clients = sum(s["customer_count"] for s in startups)
            
            # Phase distribution
            phase_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for s in startups:
                p = s["current_phase"]
                phase_counts[p] = phase_counts.get(p, 0) + 1

            cursor.execute("SELECT COUNT(*) FROM mentorship_sessions")
            total_mentor_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM simulations")
            total_simulations = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM milestones WHERE status = 'Verified'")
            verified_milestones = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM milestones")
            total_milestones = cursor.fetchone()[0]

            conn.close()

            return self._send_json({
                "summary": {
                    "total_startups": total_startups,
                    "total_monthly_revenue": total_revenue,
                    "avg_health_score": avg_health,
                    "avg_investor_readiness": avg_investor_readiness,
                    "total_team_members": total_team_members,
                    "total_paying_clients": total_paying_clients,
                    "total_mentor_sessions": total_mentor_sessions,
                    "total_simulations": total_simulations,
                    "milestone_completion_rate": round((verified_milestones / total_milestones * 100), 1) if total_milestones else 0,
                    "phase_distribution": phase_counts
                }
            })

        elif path == "/api/export/csv":
            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, department, founder_name, current_phase, stage, health_score, monthly_revenue, monthly_burn, runway_months, customer_count, investor_readiness_score FROM startups")
            rows = cursor.fetchall()
            conn.close()

            csv_lines = ["ID,Startup Name,Department,Founder,Phase,Stage,Health Score,Monthly Revenue (INR),Monthly Burn (INR),Runway (Months),Paying Clients,Investor Readiness"]
            for r in rows:
                csv_lines.append(f'{r[0]},"{r[1]}","{r[2]}","{r[3]}",Phase {r[4]},"{r[5]}",{r[6]},{r[7]},{r[8]},{r[9]},{r[10]},{r[11]}')
            
            csv_data = "\n".join(csv_lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="sakec_tbi_portfolio_report.csv"')
            self.end_headers()
            self.wfile.write(csv_data.encode("utf-8"))
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
            pwd_hash = database.hash_password(password)

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
            row = cursor.fetchone()
            conn.close()

            if row:
                u_dict = dict(row)
                token = secrets.token_hex(24)
                del u_dict["password_hash"]
                SESSIONS[token] = u_dict
                return self._send_json({"token": token, "user": u_dict})
            else:
                return self._send_json({"error": "Invalid username or password"}, 401)

        elif path == "/api/logout":
            auth_header = self.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
                if token in SESSIONS:
                    del SESSIONS[token]
            return self._send_json({"status": "logged_out"})

        elif path == "/api/startups":
            if not user or user.get("role") not in ["faculty_incharge", "authority"]:
                return self._send_json({"error": "Only Faculty Incharge or Authorized Administrators can onboard new startups"}, 403)

            name = body.get("name", "").strip()
            tagline = body.get("tagline", "").strip()
            department = body.get("department", "SAKEC Engineering").strip()
            founder_name = body.get("founder_name", "").strip()
            founder_email = body.get("founder_email", "").strip()
            stage = body.get("stage", "Idea / Prototype").strip()
            current_phase = int(body.get("current_phase", 1))
            team_size = int(body.get("team_size", 2))
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not name or not founder_name:
                return self._send_json({"error": "Startup name and founder name are required"}, 400)

            conn = database.get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO startups (
                    name, tagline, department, founder_name, founder_email, current_phase,
                    health_score, stage, monthly_burn, cash_in_bank, runway_months,
                    monthly_revenue, customer_count, team_size, investor_readiness_score,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 75, ?, 30000, 300000, 10.0, 0, 0, ?, 65, ?, ?)
                """, (name, tagline, department, founder_name, founder_email, current_phase, stage, team_size, now, now))
                new_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO digital_twins (
                    startup_id, business_model, target_market, value_proposition,
                    product_roadmap, team_structure, sales_pipeline_stage, risk_assessment,
                    tech_stack, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id,
                    json.dumps({"model": "To be structured in Phase 2 USim", "pricing": "TBD"}),
                    "Initial target market segment",
                    tagline,
                    json.dumps([{"q": "Q1", "item": "Minimum Viable Product (MVP) Build", "status": "In Progress"}]),
                    json.dumps([{"role": "Founder & Lead", "name": founder_name, "dept": department}]),
                    "Early ideation and customer discovery",
                    "Execution and product-market fit risks",
                    "To be defined",
                    now
                ))

                phases = [
                    (1, "Phase 1: Startup Onboarding & Digital Twin Architecture"),
                    (2, "Phase 2: USim Unit Economics & Pricing Model Simulation"),
                    (3, "Phase 3: WorkOS Operational Deployment & Pilot Launch"),
                    (4, "Phase 4: Mentor Evaluation & Clinical/Field Audit"),
                    (5, "Phase 5: SAKEC Demo Day & Investor Pitch Readiness")
                ]
                for p_num, title in phases:
                    cursor.execute("""
                    INSERT INTO milestones (
                        startup_id, title, phase, target_date, status, created_at
                    ) VALUES (?, ?, ?, date('now', '+30 day'), ?, ?)
                    """, (new_id, title, p_num, "In Progress" if p_num == 1 else "Pending", now))

                conn.commit()
                conn.close()
                return self._send_json({"status": "success", "startup_id": new_id})
            except Exception as e:
                conn.close()
                return self._send_json({"error": str(e)}, 500)

        elif path.startswith("/api/startups/") and path.endswith("/simulate"):
            base_price = float(body.get("base_price", 1000.0))
            monthly_fixed_cost = float(body.get("monthly_fixed_cost", 50000.0))
            variable_cost_per_unit = float(body.get("variable_cost_per_unit", 100.0))
            marketing_spend = float(body.get("marketing_spend", 10000.0))
            organic_growth_rate = float(body.get("organic_growth_rate", 10.0))
            churn_rate = float(body.get("churn_rate", 3.0))
            initial_cash = float(body.get("initial_cash", 500000.0))
            initial_customers = int(body.get("initial_customers", 5))
            cac = float(body.get("cac", 2000.0))

            result = run_usim_simulation(
                base_price, monthly_fixed_cost, variable_cost_per_unit,
                marketing_spend, organic_growth_rate, churn_rate,
                initial_cash, initial_customers, cac
            )
            return self._send_json(result)

        elif path.startswith("/api/startups/") and path.endswith("/save-simulation"):
            startup_id = int(path.split("/")[3])
            scenario_name = body.get("scenario_name", "USim Scenario Projections")
            base_price = float(body.get("base_price", 1000.0))
            monthly_fixed_cost = float(body.get("monthly_fixed_cost", 50000.0))
            variable_cost_per_unit = float(body.get("variable_cost_per_unit", 100.0))
            marketing_spend = float(body.get("marketing_spend", 10000.0))
            organic_growth_rate = float(body.get("organic_growth_rate", 10.0))
            churn_rate = float(body.get("churn_rate", 3.0))
            runway_months = float(body.get("runway_months", 12.0))
            break_even_month = int(body.get("break_even_month", 6))
            projected_arr = float(body.get("projected_arr", 1200000.0))
            notes = body.get("notes", "")
            now = datetime.now().strftime("%Y-%m-%d")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO simulations (
                startup_id, scenario_name, base_price, monthly_fixed_cost, variable_cost_per_unit,
                marketing_spend, organic_growth_rate, churn_rate, runway_result_months,
                break_even_month, projected_arr, simulation_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                startup_id, scenario_name, base_price, monthly_fixed_cost, variable_cost_per_unit,
                marketing_spend, organic_growth_rate, churn_rate, runway_months,
                break_even_month, projected_arr, now, notes
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "simulation_saved"})

        elif path.startswith("/api/startups/") and path.endswith("/kpis"):
            startup_id = int(path.split("/")[3])
            month = body.get("month", datetime.now().strftime("%Y-%m"))
            revenue = float(body.get("revenue", 0.0))
            burn_rate = float(body.get("burn_rate", 0.0))
            active_users = int(body.get("active_users", 0))
            paying_customers = int(body.get("paying_customers", 0))
            cac = float(body.get("cac", 0.0))
            ltv = float(body.get("ltv", 0.0))
            notes = body.get("notes", "")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO kpi_records (
                startup_id, month, revenue, burn_rate, active_users, paying_customers, cac, ltv, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (startup_id, month, revenue, burn_rate, active_users, paying_customers, cac, ltv, notes, now))

            cursor.execute("""
            UPDATE startups SET monthly_revenue = ?, monthly_burn = ?, customer_count = ?, updated_at = ? WHERE id = ?
            """, (revenue, burn_rate, paying_customers, now, startup_id))

            conn.commit()
            conn.close()
            return self._send_json({"status": "kpi_recorded"})

        elif path.startswith("/api/startups/") and path.endswith("/milestones"):
            startup_id = int(path.split("/")[3])
            title = body.get("title", "").strip()
            phase = int(body.get("phase", 1))
            target_date = body.get("target_date", datetime.now().strftime("%Y-%m-%d"))
            status = body.get("status", "Pending")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO milestones (startup_id, title, phase, target_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (startup_id, title, phase, target_date, status, now))
            conn.commit()
            conn.close()
            return self._send_json({"status": "milestone_created"})

        elif path == "/api/mentorship":
            startup_id = int(body.get("startup_id", 1))
            mentor_name = body.get("mentor_name", user.get("full_name", "Mentor") if user else "Mentor")
            mentor_email = body.get("mentor_email", user.get("email", "") if user else "")
            session_date = body.get("session_date", datetime.now().strftime("%Y-%m-%d"))
            focus_area = body.get("focus_area", "General Operational Review")
            feedback = body.get("feedback", "")
            health_rating = int(body.get("health_rating", 4))
            action_items = body.get("action_items", "")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO mentorship_sessions (
                startup_id, mentor_name, mentor_email, session_date, focus_area, feedback,
                health_rating, action_items, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?)
            """, (startup_id, mentor_name, mentor_email, session_date, focus_area, feedback, health_rating, action_items, now))

            cursor.execute("SELECT AVG(health_rating) FROM mentorship_sessions WHERE startup_id = ?", (startup_id,))
            avg_rating = cursor.fetchone()[0] or 4.0
            new_health = min(98, max(50, int(avg_rating * 18 + 10)))
            cursor.execute("UPDATE startups SET health_score = ?, updated_at = ? WHERE id = ?", (new_health, now, startup_id))

            conn.commit()
            conn.close()
            return self._send_json({"status": "mentorship_recorded", "new_health_score": new_health})

        return self._send_json({"error": "Endpoint not found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()
        user = self._get_auth_user()

        if path.startswith("/api/startups/") and path.endswith("/digital-twin"):
            startup_id = int(path.split("/")[3])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            bm = body.get("business_model")
            tm = body.get("target_market")
            vp = body.get("value_proposition")
            pr = body.get("product_roadmap")
            ts = body.get("team_structure")
            sp = body.get("sales_pipeline_stage")
            ra = body.get("risk_assessment")
            tech = body.get("tech_stack")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE digital_twins SET
                business_model = COALESCE(?, business_model),
                target_market = COALESCE(?, target_market),
                value_proposition = COALESCE(?, value_proposition),
                product_roadmap = COALESCE(?, product_roadmap),
                team_structure = COALESCE(?, team_structure),
                sales_pipeline_stage = COALESCE(?, sales_pipeline_stage),
                risk_assessment = COALESCE(?, risk_assessment),
                tech_stack = COALESCE(?, tech_stack),
                updated_at = ?
            WHERE startup_id = ?
            """, (
                json.dumps(bm) if isinstance(bm, (dict, list)) else bm,
                tm, vp,
                json.dumps(pr) if isinstance(pr, list) else pr,
                json.dumps(ts) if isinstance(ts, list) else ts,
                sp, ra, tech, now, startup_id
            ))
            conn.commit()
            conn.close()
            return self._send_json({"status": "digital_twin_updated"})

        elif path.startswith("/api/startups/") and len(path.split("/")) == 4:
            startup_id = int(path.split("/")[3])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = database.get_db()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM startups WHERE id = ?", (startup_id,))
            current = cursor.fetchone()
            if not current:
                conn.close()
                return self._send_json({"error": "Startup not found"}, 404)

            if user and user.get("role") == "founder" and user.get("startup_id") != startup_id:
                conn.close()
                return self._send_json({"error": "Forbidden: You can only modify your own startup"}, 403)

            name = body.get("name", current["name"])
            tagline = body.get("tagline", current["tagline"])
            current_phase = int(body.get("current_phase", current["current_phase"]))
            stage = body.get("stage", current["stage"])
            monthly_burn = float(body.get("monthly_burn", current["monthly_burn"]))
            cash_in_bank = float(body.get("cash_in_bank", current["cash_in_bank"]))
            monthly_revenue = float(body.get("monthly_revenue", current["monthly_revenue"]))
            customer_count = int(body.get("customer_count", current["customer_count"]))
            team_size = int(body.get("team_size", current["team_size"]))
            pitch_deck_url = body.get("pitch_deck_url", current["pitch_deck_url"])
            
            net_burn = max(0, monthly_burn - monthly_revenue)
            runway = round(cash_in_bank / net_burn, 1) if net_burn > 0 else 99.0

            cursor.execute("""
            UPDATE startups SET
                name = ?, tagline = ?, current_phase = ?, stage = ?,
                monthly_burn = ?, cash_in_bank = ?, runway_months = ?,
                monthly_revenue = ?, customer_count = ?, team_size = ?,
                pitch_deck_url = ?, updated_at = ?
            WHERE id = ?
            """, (name, tagline, current_phase, stage, monthly_burn, cash_in_bank, runway, monthly_revenue, customer_count, team_size, pitch_deck_url, now, startup_id))
            
            conn.commit()
            conn.close()
            return self._send_json({"status": "startup_updated", "runway_months": runway})

        elif path.startswith("/api/milestones/"):
            milestone_id = int(path.split("/")[3])
            status = body.get("status")
            verification_notes = body.get("verification_notes")
            completion_date = body.get("completion_date")
            evidence_url = body.get("evidence_url")

            conn = database.get_db()
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE milestones SET
                status = COALESCE(?, status),
                verification_notes = COALESCE(?, verification_notes),
                completion_date = COALESCE(?, completion_date),
                evidence_url = COALESCE(?, evidence_url)
            WHERE id = ?
            """, (status, verification_notes, completion_date, evidence_url, milestone_id))
            conn.commit()
            conn.close()
            return self._send_json({"status": "milestone_updated"})

        return self._send_json({"error": "Endpoint not found"}, 404)

def run_server():
    database.init_db()
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, SAKECTBIRequestHandler)
    print(f"=====================================================================")
    print(f" SAKEC Technology Business Incubator (TBI) Management Platform")
    print(f" Developed by Dr. Rohan Appasaheb Borgalli")
    print(f" Running at http://0.0.0.0:{PORT}")
    print(f"=====================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SAKEC TBI Server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
