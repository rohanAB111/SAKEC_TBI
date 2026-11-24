"""
SAKEC Technology Business Incubator (TBI) Platform — Render + OneDrive Edition
Database Module - SQLite Engine (WAL Mode) with:
- Year-Wise Cohorts (2024-25, 2025-26, 2026-27+)
- Incubated (Pvt. Ltd. with MCA CIN & DIN) vs Pre-Incubation
- Full Founders & Interns Roster (106 records)
- Document Checklist & OneDrive Repository (linked to incubation@sakec.ac.in)
- Full RBAC User & Admin Account Management
Developed by Dr. Rohan Appasaheb Borgalli
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime

DB_PATH = os.environ.get("SAKEC_DB_PATH", "/tmp/sakec_tbi.db")

REQUIRED_DOC_TYPES = [
    ("Certificate of Incorporation (COI) & CIN", "Mandatory for Pvt. Ltd. startups"),
    ("Director DIN & KYC Documents", "Mandatory for Pvt. Ltd. directors"),
    ("Company PAN / TAN / DPIIT Startup India Certificate", "Tax & Startup India recognition"),
    ("Updated Pitch Deck (PPT / PDF)", "Latest investor & incubation presentation"),
    ("Signed SAKEC TBI Incubation Agreement / MoU", "Formal onboarding agreement"),
    ("Quarterly Progress & Financial Status Report", "Revenue, burn, milestones & traction"),
    ("Interns Attendance & Monthly Work Log", "SAKEC student interns engagement proof"),
    ("Product Prototype / Live Demo Proof", "Screenshots, demo link, or video on OneDrive")
]

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
    except sqlite3.OperationalError:
        pass
    return conn

def _create_all_tables(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL, -- 'faculty_incharge', 'authority', 'mentor', 'founder'
        startup_id INTEGER,
        designation TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS startups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        former_names TEXT DEFAULT '',
        tagline TEXT NOT NULL,
        department TEXT NOT NULL,
        academic_year TEXT NOT NULL DEFAULT '2024-25',
        active_years TEXT NOT NULL DEFAULT '2024-25',
        incubation_type TEXT NOT NULL DEFAULT 'Pre-Incubation',
        cin TEXT DEFAULT '',
        pan TEXT DEFAULT '',
        tan TEXT DEFAULT '',
        incorporation_date TEXT DEFAULT '',
        roc TEXT DEFAULT '',
        authorized_capital TEXT DEFAULT '',
        paid_up_capital TEXT DEFAULT '',
        registered_address TEXT DEFAULT '',
        directors_json TEXT DEFAULT '[]',
        founder_name TEXT NOT NULL,
        founder_email TEXT NOT NULL,
        founder_phone TEXT DEFAULT '',
        website_url TEXT DEFAULT '',
        pitch_deck_url TEXT DEFAULT '',
        onedrive_folder_url TEXT DEFAULT '',
        current_phase INTEGER NOT NULL DEFAULT 1,
        health_score INTEGER NOT NULL DEFAULT 75,
        stage TEXT NOT NULL DEFAULT 'Prototype',
        monthly_burn REAL NOT NULL DEFAULT 0,
        cash_in_bank REAL NOT NULL DEFAULT 0,
        runway_months REAL NOT NULL DEFAULT 12,
        monthly_revenue REAL NOT NULL DEFAULT 0,
        customer_count INTEGER NOT NULL DEFAULT 0,
        team_size INTEGER NOT NULL DEFAULT 2,
        investor_readiness_score INTEGER NOT NULL DEFAULT 70,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        academic_year TEXT NOT NULL DEFAULT '2026-27',
        doc_type TEXT NOT NULL,
        title TEXT NOT NULL,
        onedrive_url TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Submitted', 'Verified', 'Revision Needed'
        uploaded_by TEXT DEFAULT '',
        admin_remarks TEXT DEFAULT '',
        updated_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        academic_year TEXT NOT NULL,
        semester TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Intern',
        student_class TEXT DEFAULT '',
        department TEXT DEFAULT '',
        prn TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        timings TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS digital_twins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER UNIQUE NOT NULL,
        business_model TEXT,
        target_market TEXT,
        value_proposition TEXT,
        product_roadmap TEXT,
        team_structure TEXT,
        sales_pipeline_stage TEXT,
        risk_assessment TEXT,
        tech_stack TEXT,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        phase INTEGER NOT NULL,
        target_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        verification_notes TEXT,
        completion_date TEXT,
        evidence_url TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kpi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        revenue REAL NOT NULL DEFAULT 0,
        burn_rate REAL NOT NULL DEFAULT 0,
        active_users INTEGER NOT NULL DEFAULT 0,
        paying_customers INTEGER NOT NULL DEFAULT 0,
        cac REAL NOT NULL DEFAULT 0,
        ltv REAL NOT NULL DEFAULT 0,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        scenario_name TEXT NOT NULL,
        base_price REAL NOT NULL,
        monthly_fixed_cost REAL NOT NULL,
        variable_cost_per_unit REAL NOT NULL,
        marketing_spend REAL NOT NULL,
        organic_growth_rate REAL NOT NULL,
        churn_rate REAL NOT NULL,
        runway_result_months REAL NOT NULL,
        break_even_month INTEGER NOT NULL,
        projected_arr REAL NOT NULL,
        simulation_date TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentorship_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        mentor_name TEXT NOT NULL,
        mentor_email TEXT NOT NULL,
        session_date TEXT NOT NULL,
        focus_area TEXT NOT NULL,
        feedback TEXT NOT NULL,
        health_rating INTEGER NOT NULL DEFAULT 4,
        action_items TEXT,
        status TEXT NOT NULL DEFAULT 'Completed',
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    _create_all_tables(cursor)
    conn.commit()

    # Auto-upgrade old dummy databases (e.g. CuraDental AI) to real SAKEC TBI 2024-27 dataset
    SCHEMA_VERSION = "2026.11.v3_real_sakec_data"
    needs_reseed = False
    try:
        row = cursor.execute("SELECT value FROM settings WHERE key = 'schema_version'").fetchone()
        has_real = cursor.execute("SELECT COUNT(*) FROM startups WHERE name = 'RSPY Tech Private Limited'").fetchone()[0]
        if not row or row[0] != SCHEMA_VERSION or has_real == 0:
            needs_reseed = True
    except Exception:
        needs_reseed = True

    if needs_reseed:
        for tbl in ("mentorship_sessions", "simulations", "kpi_records", "milestones", "digital_twins", "interns", "documents", "users", "startups", "settings"):
            cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
        conn.commit()
        conn.close()
        # Re-create clean schema & seed official SAKEC TBI data
        conn = get_db()
        cursor = conn.cursor()
        # Re-run DDL by calling _create_tables_and_seed
        _create_all_tables(cursor)
        seed_data(conn)
        cursor.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('schema_version', ?, ?)", (SCHEMA_VERSION, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

    conn.close()

def provision_default_documents(cursor, startup_id, academic_year, incubation_type, now, prefilled=None):
    prefilled = prefilled or {}
    for doc_type, desc in REQUIRED_DOC_TYPES:
        if incubation_type != "Incubated (Pvt. Ltd.)" and ("COI" in doc_type or "DIN" in doc_type):
            continue
        url = prefilled.get(doc_type, "")
        status = "Verified" if url else "Pending"
        cursor.execute("""
        INSERT INTO documents (startup_id, academic_year, doc_type, title, onedrive_url, status, uploaded_by, admin_remarks, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            startup_id, academic_year, doc_type, desc, url, status,
            "SAKEC TBI Admin" if url else "",
            "Initial record verified on onboarding" if url else "Awaiting founder upload to incubation@sakec.ac.in OneDrive",
            now
        ))


def seed_data(conn):
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Settings: incubation@sakec.ac.in OneDrive Master Upload Link
    settings = [
        ("onedrive_account", "incubation@sakec.ac.in", now),
        ("onedrive_master_upload_url", os.environ.get("ONEDRIVE_UPLOAD_URL", "https://onedrive.live.com/"), now),
        ("institution_name", "Shah & Anchor Kutchhi Engineering College (SAKEC), Chembur, Mumbai", now),
        ("faculty_incharge", "Dr. Rohan Appasaheb Borgalli", now),
        ("principal_name", "Dr. Bhavesh Patel", now)
    ]
    cursor.executemany("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)", settings)

    # 1. Seed 9 real SAKEC TBI startups (2024-25, 2025-26, 2026-27)
    startups = [
        (
            1, "RSPY Tech Private Limited", "RSPY TECH",
            "Software engineering, digital media tech, and custom IT solutions company incubated at SAKEC TBI.",
            "Computer Engineering", "2024-25", "2024-25", "Incubated (Pvt. Ltd.)",
            "U62099MH2025PTC444335", "AAOCR4820Q", "MUMR53054B", "2025-04-01", "RoC-Mumbai I",
            "₹4,99,990", "₹1,00,000", "1/C/1 Tolaram Nagar, Chembur Camp, Mumbai, Maharashtra - 400074",
            json.dumps([
                {"name": "RAJAS MANOJ CHAUDHARI", "din": "11030963", "designation": "Director", "appointment_date": "2025-04-01"},
                {"name": "YOGESH RAJESH PRASAD VISHWAKARMA", "din": "11030964", "designation": "Director", "appointment_date": "2025-04-01"}
            ]),
            "Rajas Manoj Chaudhari & Yogesh Vishwakarma", "rajas.chaudhari16124@sakec.ac.in", "8828463266",
            "https://www.falconebiz.com/company/RSPY-TECH-PRIVATE-LIMITED-U62099MH2025PTC444335", "", "",
            4, 88, "Incorporated & Active Operations", 45000.0, 450000.0, 15.0, 65000.0, 8, 9, 82, now, now
        ),
        (
            2, "Lunar Finis Private Limited", "Lunar Pvt. Ltd.",
            "AI-guided mutual fund and SIP recommendation platform for first-time investors and young professionals.",
            "AI & Data Science", "2024-25", "2024-25,2025-26,2026-27", "Incubated (Pvt. Ltd.)",
            "U62099MH2024PTC433392", "", "", "2024-10-10", "RoC-Mumbai",
            "₹10,00,000", "₹10,000", "105, 2nd Floor, Om Shiv CHS, JK Bhasin Marg, GTB Nagar, Sion, Antop Hill, Mumbai, Maharashtra - 400037",
            json.dumps([
                {"name": "KEERAT SINGH HARVINDER SINGH KHANDPUR", "din": "10804548", "designation": "Director", "appointment_date": "2024-10-10"},
                {"name": "HARVINDER SINGH GURBACHAN SINGH KHANDPUR", "din": "Verify on MCA", "designation": "Director", "appointment_date": "2024-10-10"}
            ]),
            "Keerat Singh Khandpur", "keerat.khandpur18507@sakec.ac.in", "8169437806",
            "https://www.tofler.in/lunar-finis-private-limited/company/U62099MH2024PTC433392",
            "https://docs.google.com/document/d/1k1a2zLqCazgQDb8nk6dv8yY4o7mvcrHwJ5XiCqWMM_w/edit", "",
            4, 84, "MVP & Regulatory Compliance (NISM/ARN)", 2100.0, 102900.0, 24.0, 0.0, 0, 4, 78, now, now
        ),
        (
            3, "Genovia Solutions Private Limited", "SPIRO / SPIRO Edu Pvt. Ltd.",
            "Computer programming, EdTech software, and IT consultancy platform (transitioned from SPIRO in 2024-25 to incorporated Pvt. Ltd. in Sep 2025).",
            "AI & Data Science", "2024-25", "2024-25,2025-26,2026-27", "Incubated (Pvt. Ltd.)",
            "U62099MH2025PTC457921", "", "", "2025-09-24", "RoC-Mumbai II",
            "₹1,00,000", "₹5,000", "Saidarshan Appt, Block No-106, Station Pada, Kulgaon, Ambarnath, Thane, Maharashtra - 421503",
            json.dumps([
                {"name": "SHUBHAM RAJESH THAKUR", "din": "11065485", "designation": "Director", "appointment_date": "2025-09-24"},
                {"name": "VEDANGI SUBHASH MHATRE", "din": "11315697", "designation": "Director", "appointment_date": "2025-09-24"},
                {"name": "SMIT SHAM DALVI", "din": "11315696", "designation": "Director", "appointment_date": "2025-09-24"}
            ]),
            "Shubham Rajesh Thakur", "shubham.thakur18369@sakec.ac.in", "8452976481",
            "https://www.falconebiz.com/company/GENOVIA-SOLUTIONS-PRIVATE-LIMITED-U62099MH2025PTC457921",
            "https://www.canva.com/design/DAGeTP8iusk/awNHYJcrYOUyLzcqR2-hCQ/edit", "",
            4, 87, "Incorporated & Scaling Operations", 35000.0, 320000.0, 12.0, 50000.0, 10, 10, 81, now, now
        ),
        (
            4, "ROVER", "ROVER Ride-Hailing",
            "Zero-commission subscription-based ride-hailing platform (₹99/day or ₹2,599/month for drivers; 15-25% lower fares and capped 1.3x surge for riders).",
            "SAKEC Student Venture", "2024-25", "2024-25", "Pre-Incubation",
            "", "", "", "", "", "", "", "", json.dumps([]),
            "Arpan Gowda", "arpan.gowda16236@sakec.ac.in", "", "", "Rover.pptx", "",
            2, 74, "Pre-Incubation / React Native App Development", 25000.0, 150000.0, 6.0, 0.0, 0, 2, 68, now, now
        ),
        (
            5, "Advizy", "Mentorix",
            "Student-led mentorship, advisory, and career guidance tech venture (transitioned from Mentorix in 2024-25 Odd Sem to Advizy).",
            "AI & Data Science", "2024-25", "2024-25,2025-26", "Pre-Incubation",
            "", "", "", "", "", "", "", "", json.dumps([]),
            "Vivek Akate", "vivek.17332@sakec.ac.in", "9307414112", "", "", "",
            3, 79, "Pre-Incubation / Prototype & Pilot", 20000.0, 120000.0, 8.0, 10000.0, 5, 7, 70, now, now
        ),
        (
            6, "Harmocare", "",
            "Healthcare and wellness technology startup built at SAKEC TBI (founded by Sumedh Kolte in 2024-26; led by Mustafa Shabbir Halvadwala in 2026-27).",
            "Information Technology", "2024-25", "2024-25,2025-26,2026-27", "Pre-Incubation",
            "", "", "", "", "", "", "", "", json.dumps([]),
            "Sumedh Kolte / Mustafa Shabbir Halvadwala", "sumedh.17074@sakec.ac.in", "7499894278",
            "", "https://www.canva.com/design/DAGemZqMzbI/HyCHxN3MlN1WvMpMpP_vSg/edit", "",
            3, 80, "Pre-Incubation / Product Validation", 22000.0, 160000.0, 9.0, 12000.0, 4, 8, 72, now, now
        ),
        (
            7, "Dashfit Private Limited", "Dashfit OS",
            "AI-powered muscle-first workout and diet planner with a patented algorithm over 230+ exercises measuring both calories and muscle activation.",
            "External / Chembur Incubatee (HealthTech & AI)", "2025-26", "2025-26", "Incubated (Pvt. Ltd.)",
            "U86900MH2025PTC445049", "", "", "2025-04-08", "RoC-Mumbai I",
            "₹5,00,000", "₹1,00,000", "A2/1103, Shree Saraswati CHSL, Chembur, Mumbai, Maharashtra - 400071",
            json.dumps([
                {"name": "SARITA DASH", "din": "11011290", "designation": "Managing Director", "appointment_date": "2025-04-08"},
                {"name": "SHASWAT DASH", "din": "11220029", "designation": "Director (Founder & CEO)", "appointment_date": "2025-07-30"}
            ]),
            "Shaswat Dash (CEO) & Bhushan Rajput (CTO)", "shaswat@dashfit.in", "+91-9920847553",
            "https://www.falconebiz.com/company/DASHFIT-PRIVATE-LIMITED-U86900MH2025PTC445049",
            "Dashfit_Pitch Deck - Incubation July v2.pdf", "",
            4, 92, "Early Revenue & App Growth (2,100+ Users)", 75000.0, 950000.0, 18.0, 161333.0, 3, 4, 89, now, now
        ),
        (
            8, "Aspect AI Solutions Private Limited", "Aspect AI",
            "AI filmmaking, conversational voice AI agents, agentic workflow orchestration, and web/UI engineering studio.",
            "Electronics & Computer Science (ECS)", "2026-27", "2026-27", "Incubated (Pvt. Ltd.)",
            "U62011MH2026PTC473470", "", "", "2026-07-14", "RoC-Mumbai I",
            "₹1,00,000", "₹1,00,000", "B-15, Asha Bldg., P. No. 140, Garodia Nagar, Ghatkopar-E, Mumbai, Maharashtra - 400077",
            json.dumps([
                {"name": "HITANS RAJESH SANGHRAJKA", "din": "11823211", "designation": "Director", "appointment_date": "2026-07-14"},
                {"name": "HRIDAY MEHUL KOTHARI", "din": "11823212", "designation": "Director (Founder)", "appointment_date": "2026-07-14"}
            ]),
            "Hriday Mehul Kothari & Hitans Rajesh Sanghrajka", "hriday.kothari25@sakec.ac.in", "9920215783",
            "https://www.theaspect.ai/", "https://www.theaspect.ai/", "",
            3, 91, "Early Revenue & Enterprise Clients", 60000.0, 650000.0, 16.0, 125000.0, 5, 4, 86, now, now
        ),
        (
            9, "Sai Agro Information Technology (SAIT)", "SAIT",
            "AgriTech information technology and digital farming solutions venture under SAKEC TBI Pre-Incubation.",
            "Computer Engineering", "2026-27", "2026-27", "Pre-Incubation",
            "", "", "", "", "", "", "", "", json.dumps([]),
            "Sai Sonawane", "amol.sonawane24@sakec.ac.in", "7397820660", "", "", "",
            1, 76, "Pre-Incubation / Onboarding & Discovery", 15000.0, 100000.0, 10.0, 0.0, 0, 2, 65, now, now
        )
    ]

    cursor.executemany("""
    INSERT INTO startups (
        id, name, former_names, tagline, department, academic_year, active_years,
        incubation_type, cin, pan, tan, incorporation_date, roc, authorized_capital,
        paid_up_capital, registered_address, directors_json, founder_name, founder_email,
        founder_phone, website_url, pitch_deck_url, onedrive_folder_url, current_phase, health_score, stage,
        monthly_burn, cash_in_bank, runway_months, monthly_revenue, customer_count,
        team_size, investor_readiness_score, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, startups)

    # 2. Seed Users (Admins, Authorities, Mentors, Founders)
    users = [
        ("rohan.borgalli", hash_password("Sakec@123"), "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "faculty_incharge", None, "Faculty Incharge - SAKEC TBI (Super Admin)", 1, now),
        ("tbi.admin", hash_password("Sakec@123"), "SAKEC TBI Coordinator", "incubation@sakec.ac.in", "faculty_incharge", None, "TBI Co-Coordinator / Update Admin", 1, now),
        ("principal", hash_password("Sakec@123"), "Dr. Bhavesh Patel", "principal@sakec.ac.in", "authority", None, "Principal - SAKEC", 1, now),
        ("dean.rd", hash_password("Sakec@123"), "Dean Research & Development", "dean.rd@sakec.ac.in", "authority", None, "Dean R&D - SAKEC", 1, now),
        ("mentor.tech", hash_password("Sakec@123"), "Prof. Milind Khairnar", "milind.khairnar@sakec.ac.in", "mentor", None, "Technical & DeepTech Mentor", 1, now),
        ("mentor.biz", hash_password("Sakec@123"), "Ashwin S. (CybraneX)", "ashwin@cybranex.com", "mentor", None, "Business & Incubation Strategist", 1, now),
        ("founder.rspy", hash_password("Sakec@123"), "Rajas Chaudhari", "rajas.chaudhari16124@sakec.ac.in", "founder", 1, "Founder & Director, RSPY Tech Pvt. Ltd.", 1, now),
        ("founder.lunar", hash_password("Sakec@123"), "Keerat Singh Khandpur", "keerat.khandpur18507@sakec.ac.in", "founder", 2, "Founder & Director, Lunar Finis Pvt. Ltd.", 1, now),
        ("founder.genovia", hash_password("Sakec@123"), "Shubham Thakur", "shubham.thakur18369@sakec.ac.in", "founder", 3, "Founder & Director, Genovia Solutions Pvt. Ltd.", 1, now),
        ("founder.rover", hash_password("Sakec@123"), "Arpan Gowda", "arpan.gowda16236@sakec.ac.in", "founder", 4, "Founder, ROVER (Pre-Incubation)", 1, now),
        ("founder.advizy", hash_password("Sakec@123"), "Vivek Akate", "vivek.17332@sakec.ac.in", "founder", 5, "Founder, Advizy (Pre-Incubation)", 1, now),
        ("founder.harmocare", hash_password("Sakec@123"), "Sumedh Kolte", "sumedh.17074@sakec.ac.in", "founder", 6, "Founder, Harmocare (Pre-Incubation)", 1, now),
        ("founder.dashfit", hash_password("Sakec@123"), "Shaswat Dash", "shaswat@dashfit.in", "founder", 7, "Founder & CEO, Dashfit Pvt. Ltd.", 1, now),
        ("founder.aspectai", hash_password("Sakec@123"), "Hriday Mehul Kothari", "hriday.kothari25@sakec.ac.in", "founder", 8, "Founder & Director, Aspect AI Solutions Pvt. Ltd.", 1, now),
        ("founder.sait", hash_password("Sakec@123"), "Sai Sonawane", "amol.sonawane24@sakec.ac.in", "founder", 9, "Founder, Sai Agro Information Technology (SAIT)", 1, now)
    ]
    cursor.executemany("""
    INSERT INTO users (username, password_hash, full_name, email, role, startup_id, designation, active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # 3. Seed Required Document Checklists for all 9 startups
    prefills = {
        1: {"Certificate of Incorporation (COI) & CIN": "https://www.falconebiz.com/company/RSPY-TECH-PRIVATE-LIMITED-U62099MH2025PTC444335"},
        2: {"Certificate of Incorporation (COI) & CIN": "https://www.tofler.in/lunar-finis-private-limited/company/U62099MH2024PTC433392",
            "Updated Pitch Deck (PPT / PDF)": "https://docs.google.com/document/d/1k1a2zLqCazgQDb8nk6dv8yY4o7mvcrHwJ5XiCqWMM_w/edit"},
        3: {"Certificate of Incorporation (COI) & CIN": "https://www.falconebiz.com/company/GENOVIA-SOLUTIONS-PRIVATE-LIMITED-U62099MH2025PTC457921",
            "Updated Pitch Deck (PPT / PDF)": "https://www.canva.com/design/DAGeTP8iusk/awNHYJcrYOUyLzcqR2-hCQ/edit"},
        6: {"Updated Pitch Deck (PPT / PDF)": "https://www.canva.com/design/DAGemZqMzbI/HyCHxN3MlN1WvMpMpP_vSg/edit"},
        7: {"Certificate of Incorporation (COI) & CIN": "https://www.falconebiz.com/company/DASHFIT-PRIVATE-LIMITED-U86900MH2025PTC445049"},
        8: {"Certificate of Incorporation (COI) & CIN": "https://www.falconebiz.com/company/ASPECT-AI-SOLUTIONS-PRIVATE-LIMITED-U62011MH2026PTC473470",
            "Product Prototype / Live Demo Proof": "https://www.theaspect.ai/"}
    }
    for s in startups:
        provision_default_documents(cursor, s[0], s[5], s[7], now, prefills.get(s[0]))

    # 4. Seed Complete Founders & Interns Roster (106 records from Excel)
    interns = [
        (1, "2024-25", "Odd Sem", "Mr. Rajas Chaudhari", "Founder", "BE3", "Computer Engineering", "21UF16124CM006", "8828463266", "rajas.chaudhari16124@sakec.ac.in", "1pm - 5pm", "", "2024-12-31", now),
        (1, "2024-25", "Odd Sem", "Mr. Yogesh Vishwakarma", "Founder", "BE3", "Computer Engineering", "21UF1616ICM063", "9920036166", "yogesh.vishwakarma16161@sakec.ac.in", "1pm - 5pm", "", "2024-12-31", now),
        (1, "2024-25", "Odd Sem", "Ms. Hrutika Adepu", "Intern", "TE1", "Electronics and Computer Science", "22UF17107EC001", "9004746080", "", "1pm - 5pm", "", "", now),
        (1, "2024-25", "Odd Sem", "Mr. Anish Khadtare", "Intern", "Alumni Batch 2023-24", "Computer Engineering", "20UF15636CM083", "7304835568", "anish.khadtare15636@sakec.ac.in", "1pm - 5pm", "", "", now),
        (1, "2024-25", "Odd Sem", "Mr. Kshitij Sonawane", "Intern", "Alumni Batch 2023-24", "Cyber Security", "20UF15860CS042", "9920846069", "kshitij.sonawane15860@sakec.ac.in", "1pm - 5pm", "", "", now),
        (1, "2024-25", "Even Sem", "Mr. Rajas Chaudhari", "Founder", "BE3", "Computer Engineering", "21UF16124CM006", "8828463266", "rajas.chaudhari16124@sakec.ac.in", "10am - 5pm", "2025-01-01", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Mr. Yogesh Vishwakarma", "Founder", "BE3", "Computer Engineering", "21UF1616ICM063", "9920036166", "yogesh.vishwakarma16161@sakec.ac.in", "10am - 5pm", "2025-01-01", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Mr. Palak Mahesh Bhanushali", "Intern", "Drop", "Cyber Security", "22UF16974CS009", "9324177398", "palakmaheshb@gmail.com", "10am - 5pm", "2025-01-01", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Mr. Ansh Gala", "Intern", "SE4", "Computer Engineering", "23UF17997CM079", "7506453663", "ansh.17997@sakec.ac.in", "10am - 5pm", "2025-01-01", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Sujal Kishor Patil", "Intern", "TE9", "Computer Engineering", "22UF17067CM166", "7208673273", "sujal.17067@sakec.ac.in", "10am - 5pm", "2025-02-25", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Soham Wanganekar", "Intern", "TE4", "Computer Engineering", "22UF17366CM125", "9076180205", "soham.17366@sakec.ac.in", "10am - 5pm", "2025-02-25", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Jash Devkar Paresh", "Intern", "TE4", "Computer Engineering", "22UF17164CM076", "9004262865", "jash.17164@sakec.ac.in", "10am - 5pm", "2025-02-25", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Deeksha Upadhyay", "Intern", "TE4", "Computer Engineering", "22UF17410CM120", "9322508642", "deeksha.17410@sakec.ac.in", "10am - 5pm", "2025-02-25", "2025-06-30", now),
        (1, "2024-25", "Even Sem", "Nityaa Bhanushali", "Intern", "TE4", "Computer Engineering", "22UF17303CM132", "7977191113", "nityaa.17303@sakec.ac.in", "10am - 5pm", "2025-02-25", "2025-06-30", now),
        (2, "2024-25", "Odd Sem", "Mr. Keerat Singh", "Founder", "SE13", "AI & DS", "23UF18507AI026", "8169437806", "keerat.khandpur18507@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (2, "2024-25", "Odd Sem", "Krish Kamlesh Jain", "Intern", "SE-05 IT", "IT", "23UF17958IT025", "8983419163", "krish.17958@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (2, "2024-25", "Odd Sem", "Kush Bhanushali", "Intern", "BE-13 AI&DS", "AI & DS", "21UF16203AI003", "9082787023", "kush.bhanushali16203@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (2, "2024-25", "Even Sem", "Mr. Keerat Singh", "Founder", "SE13 AI&DS", "AI & DS", "23UF18507AI026", "8169437806", "keerat.khandpur18507@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (2, "2024-25", "Even Sem", "Krish Kamlesh Jain", "Intern", "SE-05 IT", "IT", "23UF17958IT025", "8983419163", "krish.17958@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (2, "2024-25", "Even Sem", "Kush Bhanushali", "Intern", "BE-13 AI&DS", "AI & DS", "21UF16203AI003", "9082787023", "kush.bhanushali16203@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (2, "2024-25", "Even Sem", "Anandkumar Suthar", "Intern", "BE-9", "COMPS", "21UF16664CM119", "6367982034", "anandkumar.suthar16664@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (2, "2025-26", "Odd Sem", "Mr. Keerat Singh", "Founder", "TY13 AI&DS", "AI & DS", "23UF18507AI026", "8169437806", "keerat.khandpur18507@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Hetvi Bhanushali", "Intern", "SY-03 CM", "COMPS", "124BTCM1025", "9137780975", "hetvi.bhanushali24@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Parth Thambe", "Intern", "SY-13", "AI & DS", "21UF169131I057", "7715038102", "parth.thambe16913@sakec.ac.in", "10am - 5 pm", "2025-07-01", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Shravani Shewale", "Intern", "SY-13", "AI & DS", "23UF18480AI051", "8879726539", "shravani.shewale18480@sakec.ac.in", "10 am - 5 pm", "2025-10-06", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Hari Santosh Bait", "Intern", "TY-09", "COMPS", "23UF18429CM065", "9137108055", "hari.bait18429@sakec.ac.in", "10 am - 5 pm", "2025-10-06", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Mr. Adarsh Kumar Kanaujiya", "Intern", "TY09", "COMPS", "23UF18279CM090", "9930410665", "adarshkumar.18279@sakec.ac.in", "10am - 5pm", "2025-10-06", "2025-12-31", now),
        (2, "2025-26", "Odd Sem", "Shravan Kailas Padhar", "Intern", "TY-09", "COMPS", "23UF17927CM162", "9322765756", "shravan.17927@sakec.ac.in", "10am - 5pm", "2025-10-06", "2025-12-31", now),
        (2, "2026-27", "Odd Sem", "Mr. Keerat Singh", "Founder", "Final Year13", "AI & DS", "23UF18507AI026", "8169437806", "keerat.khandpur18507@sakec.ac.in", "10 am - 5 pm", "2026-08-01", "2026-12-31", now),
        (2, "2026-27", "Odd Sem", "Sairaj Sawant", "Intern", "Passed Out", "ECS", "-", "9892695199", "sairaj.17192@sakec.ac.in", "10 am - 5 pm", "2026-10-01", "2026-12-31", now),
        (2, "2026-27", "Odd Sem", "Svara Chheda", "Intern", "Final Year", "IT", "23UF17972IT073", "8850948873", "svara.17972@sakec.ac.in", "10 am - 5 pm", "2026-10-01", "2026-12-31", now),
        (2, "2026-27", "Odd Sem", "Sumit Dubey", "Intern", "Final Year", "IT", "23UF18492IT078", "7021931245", "sumit.dubey18492@sakec.ac.in", "10 am - 5 pm", "2026-10-01", "2026-12-31", now),
        (3, "2024-25", "Odd Sem", "Mr. Shubham Thakur", "Founder", "SE13", "AI & DS", "23UF18369AI055", "8452976481", "shubham.thakur18369@sakec.ac.in", "10.50AM - 4.45PM", "2024-07-16", "2024-12-31", now),
        (3, "2024-25", "Odd Sem", "Ms. Vedangi Mhatre", "Intern", "SE2", "ECS", "23UF18193EC097", "8104187587", "vedangi.18193@sakec.ac.in", "11AM - 4.45PM", "2024-07-17", "2024-12-31", now),
        (3, "2024-25", "Odd Sem", "Ms. Shravani Shewale", "Intern", "SE13", "AI & DS", "23UF18480AI051", "8879726539", "shravani.shewale18480@sakec.ac.in", "11AM - 4.45PM", "2024-07-17", "2024-12-31", now),
        (3, "2024-25", "Even Sem", "Mr. Shubham Thakur", "Founder", "SE13", "AI & DS", "23UF18369AI055", "8452976481", "shubham.thakur18369@sakec.ac.in", "10.00 AM - 5 PM", "2024-07-16", "2025-06-30", now),
        (3, "2024-25", "Even Sem", "Ms. Vedangi Mhatre", "Intern", "SE2", "ECS", "23UF18193EC097", "8104187587", "vedangi.18193@sakec.ac.in", "10.00 AM - 5 PM", "2024-07-17", "2025-06-30", now),
        (3, "2024-25", "Even Sem", "Mr. Tejas Surendra Najare", "Intern", "SE7", "EXTC", "124BTEX2008", "7028588336", "tejas.najare24@sakec.ac.in", "10.00 AM - 5 PM", "2024-12-16", "2025-06-30", now),
        (3, "2024-25", "Even Sem", "Ms. Shravani Kurhade", "Intern", "SE 15", "Cyber Security", "124BTCS2006", "8591857612", "shravani.kurhade24@sakec.ac.in", "10.00 AM - 5 PM", "2025-01-18", "2025-05-18", now),
        (3, "2024-25", "Even Sem", "Mr. Deep Chaudhari", "Intern", "FE2", "COMPS", "124BTCM1118", "7738266248", "deep.chaudhari@sakec.ac.in", "10.00 AM - 5 PM", "2025-01-08", "2025-05-18", now),
        (3, "2024-25", "Even Sem", "Ms. Shravani Shewale", "Intern", "SE13", "AI & DS", "23UF18480AI051", "8879726539", "shravani.shewale18480@sakec.ac.in", "10.00 AM - 5 PM", "2024-07-17", "2025-06-30", now),
        (3, "2024-25", "Even Sem", "Mr. Nitesh Vyas", "Intern", "TY 4", "COMPS", "22UF17013CM123", "8291236232", "nitesh.17013@sakec.ac.in", "10am - 5pm", "2025-03-12", "2025-09-12", now),
        (3, "2024-25", "Even Sem", "Mr. Kunal Sharma", "Intern", "TY 4", "COMPS", "22UF17035CM179", "9221489555", "kunal.17035@sakec.ac.in", "10am - 5pm", "2025-03-12", "2025-09-12", now),
        (3, "2024-25", "Even Sem", "Mr. Smit Dalvi", "Intern", "FY 2", "COMPS", "124BTCM2", "7718938669", "smit.dalvi24@sakec.ac.in", "10am - 5pm", "2025-03-12", "2025-12-12", now),
        (3, "2025-26", "Odd Sem", "Mr. Shubham Thakur", "Founder", "SY13", "AI & DS", "23UF18369AI055", "8452976481", "shubham.thakur18369@sakec.ac.in", "10.00 AM - 5 PM", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Ms. Vedangi Mhatre", "Founder", "SY2", "ECS", "23UF18193EC097", "8104187587", "vedangi.18193@sakec.ac.in", "10.00 AM - 5 PM", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Tejas Surendra Najare", "Intern", "TY7", "EXTC", "124BTEX2008", "7028588336", "tejas.najare24@sakec.ac.in", "10.00 AM - 5 PM", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Ms. Khushi Koli", "Intern", "SYIT1", "IT", "124BTIT1138", "9930980921", "khushi.koli241@sakec.ac.in", "10.00 AM - 5 PM", "2025-08-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Deep Chaudhari", "Intern", "SY2", "COMPS", "124BTCM1118", "7738266248", "deep.chaudhari@sakec.ac.in", "10.00 AM - 5 PM", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Ms. Shravani Shewale", "Intern", "TY13", "AI & DS", "23UF18480AI051", "8879726539", "shravani.shewale18480@sakec.ac.in", "10.00 AM - 5 PM", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Nitesh Vyas", "Intern", "BY 4", "COMPS", "22UF17013CM123", "8291236232", "nitesh.17013@sakec.ac.in", "10am - 5pm", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Kunal Sharma", "Intern", "BY 4", "COMPS", "22UF17035CM179", "9221489555", "kunal.17035@sakec.ac.in", "10am - 5pm", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Smit Dalvi", "Founder", "SY 2", "COMPS", "124BTCM2", "7718938669", "smit.dalvi24@sakec.ac.in", "10am - 5pm", "2025-07-01", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Adarsh Kumar Kanaujiya", "Intern", "TY09", "COMPS", "23UF18279CM090", "9930410665", "adarshkumar.18279@sakec.ac.in", "10am - 5pm", "2025-06-16", "2025-12-31", now),
        (3, "2025-26", "Odd Sem", "Mr. Sandeep Prajapati", "Intern", "SY2", "COMPS", "124BTCM1022", "7208157015", "sandeep.prajapati24@sakec.ac.in", "10am - 5pm", "2025-06-16", "2025-12-16", now),
        (3, "2026-27", "Odd Sem", "Mr. Shubham Thakur", "Founder", "TY13", "AI & DS", "23UF18369AI055", "8452976481", "shubham.thakur18369@sakec.ac.in", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Atharva Ghuge", "Intern", "TY", "COMPS", "124BTCM1063", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Haziq Irfan Landge", "Intern", "TY", "COMPS", "124BTCM1193", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Parshwa Lalit Gosrani", "Intern", "TY", "EXTC", "124BTEX1071", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Harsh Gahankar", "Intern", "TY", "COMPS", "124BTCM1169", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Vrunda Shah", "Intern", "TY", "IT", "124BTIT1142", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Praptee Panchal", "Intern", "TY", "AI & DS", "124BTAI1015", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Upen Satish Gupta", "Intern", "TY", "AI & DS", "124BTAI1058", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Hardi Jain", "Intern", "TY", "AI & DS", "124BTAI1025", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (3, "2026-27", "Odd Sem", "Maahi Shah", "Intern", "TY", "COMPS", "124BTCM1142", "", "", "10.00 AM - 5 PM", "2026-10-01", "2026-12-31", now),
        (4, "2024-25", "Even Sem", "Arpan Gowda", "Founder", "Student", "SAKEC", "", "", "arpan.gowda16236@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (5, "2024-25", "Odd Sem", "Vivek Akate", "Founder", "TE 13", "AI & DS", "22UF17332AI002", "9307414112", "vivek.17332@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Odd Sem", "Sheedhukumar Achary", "Intern", "TE 13", "AI & DS", "22UF17052AI001", "7208387440", "sheedhukumar.17052@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Odd Sem", "Anshul Chauhan", "Intern", "TE 13", "AI & DS", "22UF17389AI007", "8529764458", "anshul.17389@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Odd Sem", "Ritesh Kolte", "Intern", "TE 1", "ECS", "22UF17329EC023", "9309918200", "ritesh.17329@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Odd Sem", "Gurdev Singh Dhanjal", "Intern", "TE9", "COMPS", "22UF17092CM139", "7498169515", "gurdev.17092@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Odd Sem", "Abhishek Ravindra Patil", "Intern", "SE4", "COMPS", "124BTCM2007", "9321997116", "abhishek.patil24@sakec.ac.in", "10 am - 5 pm", "2024-07-01", "2024-12-31", now),
        (5, "2024-25", "Even Sem", "Sumeet Ravindra Devrukhkar", "Intern", "SY4", "COMPS", "23UF17758CM073", "9653166236", "sumeet.17758@sakec.ac.in", "10 am - 5 pm", "2025-04-15", "2025-06-30", now),
        (5, "2025-26", "Odd Sem", "Vivek Akate", "Founder", "BY13", "AI & DS", "22UF17332AI002", "9307414112", "vivek.17332@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Sheedhukumar Achary", "Intern", "BY 13", "AI & DS", "22UF17052AI001", "7208387440", "sheedhukumar.17052@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Anshul Chauhan", "Intern", "BY 13", "AI & DS", "22UF17389AI007", "8529764458", "anshul.17389@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Ritesh Kolte", "Intern", "BY 1", "ECS", "22UF17329EC023", "9309918200", "ritesh.17329@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Varadraj Mokashi", "Intern", "TY09", "COMPS", "23UF17996CM098", "8652219255", "varadraj.17996@sakec.ac.in", "10 am - 5 pm", "2025-07-18", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Dwijesh Manoj Mistry", "Intern", "TY09", "COMPS", "23UF17728CM097", "7700021159", "dwijesh.17728@sakec.ac.in", "10 am - 5 pm", "2025-07-18", "2025-12-31", now),
        (5, "2025-26", "Odd Sem", "Sumeet Ravindra Devrukhkar", "Intern", "TY04", "COMPS", "23UF17758CM073", "9653166236", "sumeet.17758@sakec.ac.in", "10 am - 5 pm", "2025-07-18", "2025-12-31", now),
        (6, "2024-25", "Even Sem", "Sumedh Kolte", "Founder", "TE-5", "IT", "22UF17074IT026", "7499894278", "sumedh.17074@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Pritam Waghoskar", "Intern", "TE-3", "COMPS", "22UF17065CM062", "8652098965", "pritam.17065@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Harsh Selokar", "Intern", "TE-3", "COMPS", "22UF17660CM049", "9766198426", "harsh.selokar17660@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Ritu Wankhede", "Intern", "TE-3", "COMPS", "22UF17502CM188", "7666942047", "ritu.17502@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Atharva Sable", "Intern", "TE-1", "ECS", "22UF17367EC044", "9967607699", "atharva.17367@sakec.ac.in", "10 am - 5 pm", "2025-01-01", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Nitish Yadav", "Intern", "TE-4", "COMPS", "22UF16961CM126", "9321776392", "nitish.16961@sakec.ac.in", "10 am - 5 pm", "2025-03-04", "2025-06-30", now),
        (6, "2024-25", "Even Sem", "Shresth Gupta", "Intern", "TE-6", "IT", "23US18588IT010", "7506992248", "shresth.gupta18588@sakec.ac.in", "11 am - 6pm", "2025-03-18", "2025-06-30", now),
        (6, "2025-26", "Odd Sem", "Sumedh Kolte", "Founder", "BY-5", "IT", "22UF17074IT026", "7499894278", "sumedh.17074@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Pritam Waghoskar", "Intern", "BY-3", "COMPS", "22UF17065CM062", "8652098965", "pritam.17065@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Harsh Selokar", "Intern", "BY-3", "COMPS", "22UF17660CM049", "9766198426", "harsh.selokar17660@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Ritu Wankhede", "Intern", "BY-3", "COMPS", "22UF17502CM188", "7666942047", "ritu.17502@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Atharva Sable", "Intern", "BY-1", "ECS", "22UF17367EC044", "9967607699", "atharva.17367@sakec.ac.in", "10 am - 5 pm", "2025-07-01", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Prem Rathod", "Intern", "TY-15", "Cyber Security", "124BTCS2003", "9867493393", "prem.rathod24@sakec.ac.in", "10 am - 5 pm", "2025-08-08", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Suman Khavadia", "Intern", "TY-4", "COMPS", "23UF17804CM154", "9004070347", "suman.17804@sakec.ac.in", "10 am - 5 pm", "2025-08-11", "2025-12-31", now),
        (6, "2025-26", "Odd Sem", "Krati Jain", "Intern", "TY-4", "COMPS", "23UF18335CM147", "8788039104", "krati.18335@sakec.ac.in", "10 am - 5 pm", "2025-08-22", "2025-12-31", now),
        (6, "2026-27", "Odd Sem", "Halvadwala Mustafa Shabbir", "Founder", "", "SAKEC", "", "", "", "10 am - 5 pm", "2026-08-01", "2026-12-31", now),
        (7, "2025-26", "Odd Sem", "Shaswat Dash", "Founder", "CEO", "External / Chembur", "DIN:11220029", "+91-9920847553", "shaswat@dashfit.in", "Full-Time", "2025-07-01", "2026-06-30", now),
        (7, "2025-26", "Odd Sem", "Bhushan Rajput", "Founder", "CTO", "External / Mumbai", "-", "", "", "Full-Time", "2025-07-01", "2026-06-30", now),
        (7, "2025-26", "Odd Sem", "Sarita Dash", "Founder", "Managing Director", "External / Chembur", "DIN:11011290", "", "", "Board", "2025-04-08", "2026-06-30", now),
        (8, "2026-27", "Odd Sem", "Hriday Mehul Kothari", "Founder", "SY - 1", "ECS", "125BTEC1022", "9920215783", "hriday.kothari25@sakec.ac.in", "10 am - 5 pm", "2026-08-01", "2026-12-31", now),
        (8, "2026-27", "Odd Sem", "Hitans Rajesh Sanghrajka", "Founder", "Director", "External / Mumbai", "DIN:11823211", "9029435547", "contact@theaspect.ai", "Full-Time", "2026-07-14", "2026-12-31", now),
        (8, "2026-27", "Odd Sem", "Ms. Shravani Shewale", "Intern", "Final Year13", "AI & DS", "23UF18480AI051", "8879726539", "shravani.shewale18480@sakec.ac.in", "10.00 AM - 5 PM", "2026-08-01", "2026-11-03", now),
        (8, "2026-27", "Odd Sem", "Ms. Pallavi Batavia", "Intern", "", "COMPS", "", "", "", "10 am - 5 pm", "2026-08-01", "2026-11-03", now),
        (8, "2026-27", "Odd Sem", "Mr. Ansh Singh", "Intern", "", "EXTC", "", "", "", "10 am - 5 pm", "2026-08-01", "2026-11-03", now),
        (9, "2026-27", "Odd Sem", "Mr. Sai Sonawane", "Founder", "TY13", "COMPS", "124BTCM1048", "7397820660", "amol.sonawane24@sakec.ac.in", "10 am - 5 pm", "2026-10-01", "2026-12-31", now),
        (9, "2026-27", "Odd Sem", "Shaswat Upadhay (TBI Student)", "Intern", "BVOC", "Cyber Security", "-----", "", "", "10 am - 5 pm", "2026-08-01", "2026-12-31", now),
        (9, "2026-27", "Odd Sem", "Ms. Nupoor Mahajan", "Intern", "TY 13", "COMPS", "124BTCM1103", "9321534059", "nupoor.mahajan24@sakec.ac.in", "10 am - 5 pm", "2026-10-01", "2026-12-31", now)
    ]
    cursor.executemany("""
    INSERT INTO interns (startup_id, academic_year, semester, name, role, student_class, department, prn, phone, email, timings, start_date, end_date, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, interns)

    # 5. Seed Digital Twins, Milestones, KPIs, Simulations, Mentorship
    digital_twins = [
        (1, json.dumps({"model": "B2B IT Services & Custom Software", "pricing": "Project & Retainer Contracts", "channels": "SMEs & Institutional Clients"}),
         "Businesses and digital media clients in Mumbai.", "Full-stack engineering and IT consultancy led by SAKEC Computer Engineering founders.",
         json.dumps([{"q": "2024-25", "item": "Incubation onboarding & MCA incorporation (CIN U62099MH2025PTC444335)", "status": "Completed"}, {"q": "2025-26", "item": "Commercial IT delivery expansion", "status": "In Progress"}]),
         json.dumps([{"role": "Director (DIN: 11030963)", "name": "Rajas Manoj Chaudhari", "dept": "COMPS"}, {"role": "Director (DIN: 11030964)", "name": "Yogesh Vishwakarma", "dept": "COMPS"}]),
         "Active incorporated Pvt. Ltd. company.", "Client acquisition continuity.", "Full-Stack Web, Cloud, Software Services", now),
        (2, json.dumps({"model": "MFD Trail Commission + Paid Subscriptions + Future B2B White-Label", "pricing": "Trail commission on SIP AUM", "channels": "College students & first-time SIP investors"}),
         "First-time retail mutual fund & SIP investors across India.", "AI-guided mutual fund & SIP recommendation platform with Digio/Setu KYC.",
         json.dumps([{"q": "2024-10", "item": "Incorporated Lunar Finis Pvt. Ltd. (CIN U62099MH2024PTC433392)", "status": "Completed"}, {"q": "2025-26", "item": "NISM certification & MFD ARN registration (₹79,000 ask)", "status": "In Progress"}]),
         json.dumps([{"role": "Director (DIN: 10804548)", "name": "Keerat Singh Khandpur", "dept": "AI & DS"}, {"role": "Director", "name": "Harvinder Singh Khandpur", "dept": "Board"}]),
         "Principal screening stage; ₹79,000 funding proposal.", "AMFI/SEBI compliance & ARN registration.", "Python, LLM/AI Engine, Setu, Digio KYC", now),
        (3, json.dumps({"model": "EdTech SaaS & IT Consultancy", "pricing": "Institutional & B2B subscriptions", "channels": "Colleges & SMEs"}),
         "Students, colleges, and SMEs seeking AI-assisted software.", "Evolved from SPIRO (2024-25) to Genovia Solutions Pvt. Ltd. (Sep 2025).",
         json.dumps([{"q": "2024-25", "item": "Pre-Incubation as SPIRO", "status": "Completed"}, {"q": "2025-09", "item": "Incorporated Genovia Solutions Pvt. Ltd. (CIN U62099MH2025PTC457921)", "status": "Completed"}]),
         json.dumps([{"role": "Director (DIN: 11065485)", "name": "Shubham Thakur", "dept": "AI & DS"}, {"role": "Director (DIN: 11315697)", "name": "Vedangi Mhatre", "dept": "ECS"}, {"role": "Director (DIN: 11315696)", "name": "Smit Dalvi", "dept": "COMPS"}]),
         "Active Pvt. Ltd. venture with 10-member 2026-27 student cohort.", "First-year MCA filings & scaling.", "Full-Stack Web, AI/ML, Cloud", now),
        (4, json.dumps({"model": "Driver Subscription (₹99/day or ₹2,599/mo) + Rider Convenience Fee", "pricing": "0% commission; 15-25% lower fares; 1.3x surge cap", "channels": "Mumbai & Navi Mumbai commuters"}),
         "Urban ride-hailing market ($12B by 2028); initial focus Mumbai & Navi Mumbai.", "Driver-centric zero-commission ride-hailing platform.",
         json.dumps([{"q": "2024-25", "item": "React Native app & fare structure", "status": "In Progress"}, {"q": "Launch", "item": "1,000 driver onboarding goal", "status": "Planned"}]),
         json.dumps([{"role": "Founder", "name": "Arpan Gowda", "dept": "SAKEC"}]),
         "Pre-Incubation; ₹10L funding ask for 10% equity.", "Marketplace liquidity.", "React Native, GPS, AI Ride Matching", now),
        (5, json.dumps({"model": "Mentorship & Career Advisory Platform", "pricing": "Freemium / Cohort Subscriptions", "channels": "Engineering students"}),
         "College students seeking structured mentorship.", "Student-led mentorship platform (formerly Mentorix).",
         json.dumps([{"q": "2024-25", "item": "Launched as Mentorix -> Advizy", "status": "Completed"}, {"q": "2025-26", "item": "7-member student intern team", "status": "In Progress"}]),
         json.dumps([{"role": "Founder", "name": "Vivek Akate", "dept": "AI & DS"}]),
         "Pre-Incubation pilot stage.", "Incorporation & monetization.", "Web Platform, AI Matching", now),
        (6, json.dumps({"model": "Digital Health & Wellness Platform", "pricing": "Subscription / Partner Clinics", "channels": "Wellness seekers & clinics"}),
         "Health-conscious consumers and patients.", "Accessible digital health venture incubated at SAKEC TBI.",
         json.dumps([{"q": "2024-26", "item": "Prototype & 8-member cohort", "status": "Completed"}, {"q": "2026-27", "item": "Leadership transition & validation", "status": "In Progress"}]),
         json.dumps([{"role": "Founder (2024-26)", "name": "Sumedh Kolte", "dept": "IT"}, {"role": "Founder (2026-27)", "name": "Halvadwala Mustafa Shabbir", "dept": "SAKEC"}]),
         "Pre-Incubation product validation.", "Health data privacy & incorporation.", "Web/Mobile App, Analytics", now),
        (7, json.dumps({"model": "B2C AI Planner (₹500/mo) + 1:1 Coaching (₹5,000/mo) + B2B2C Gyms", "pricing": "₹500/mo AI; ₹5,000/mo coaching", "channels": "App, 20K+ Instagram, Partner Gyms"}),
         "Global Fitness TAM $257B; Digital Fitness SAM $65.73B.", "Patented biomechanics algorithm over 230+ exercises measuring Calories & Muscle Activation.",
         json.dumps([{"q": "2025-26", "item": "2,100+ App users & 3 onboarded gyms (CIN U86900MH2025PTC445049)", "status": "Completed"}, {"q": "Next", "item": "Dashfit App 2.0 + Camera Virtual Trainer + 20 Gyms", "status": "In Progress"}]),
         json.dumps([{"role": "Founder, CEO & Director (DIN: 11220029)", "name": "Shaswat Dash", "dept": "MBA Great Lakes"}, {"role": "Co-Founder & CTO", "name": "Bhushan Rajput", "dept": "BSc CS"}, {"role": "MD (DIN: 11011290)", "name": "Sarita Dash", "dept": "Board"}]),
         "20K+ Instagram, 2,100+ app users, 1,000+ B2B gym users; Y1 Target ₹19.36L.", "B2B gym sales velocity.", "iOS/Android, Biomechanics AI, Computer Vision", now),
        (8, json.dumps({"model": "B2B AI Studio & Engineering Retainers", "pricing": "Enterprise & Commercial Contracts", "channels": "Brands & Media Houses"}),
         "Brands & enterprises adopting AI filmmaking, voice AI agents & web engineering.", "Creative + AI-first engineering studio (Somnath 1026 AD, 25K+ voice agents, 21+ agentic integrations).",
         json.dumps([{"q": "2026-07", "item": "Incorporated Aspect AI Solutions Pvt. Ltd. (CIN U62011MH2026PTC473470)", "status": "Completed"}, {"q": "2026-27", "item": "Enterprise delivery for H&M, Reliance Digital, Trends, Climb Capital", "status": "In Progress"}]),
         json.dumps([{"role": "Director & Founder (DIN: 11823212)", "name": "Hriday Mehul Kothari", "dept": "SY-1 ECS"}, {"role": "Director (DIN: 11823211)", "name": "Hitans Rajesh Sanghrajka", "dept": "Board"}]),
         "Active commercial clients (H&M, Reliance Digital, Trends, Climb Capital, Digital Jain Pathshala).", "GPU compute scaling.", "Generative Video AI, Voice AI, Agentic Workflows, Web/UI", now),
        (9, json.dumps({"model": "AgriTech Software & Advisory", "pricing": "Phase 2 USim", "channels": "Farmers & FPOs"}),
         "Agricultural communities in Maharashtra.", "AgriTech information technology venture under SAKEC TBI Pre-Incubation.",
         json.dumps([{"q": "2026-27", "item": "Pre-Incubation onboarding & field discovery", "status": "In Progress"}]),
         json.dumps([{"role": "Founder", "name": "Sai Sonawane", "dept": "TY13 COMPS"}, {"role": "Intern", "name": "Nupoor Mahajan", "dept": "TY13 COMPS"}]),
         "Phase 1 Pre-Incubation onboarding.", "Rural connectivity & adoption.", "Web/Mobile AgriTech, Data Analytics", now)
    ]
    cursor.executemany("""
    INSERT INTO digital_twins (startup_id, business_model, target_market, value_proposition, product_roadmap, team_structure, sales_pipeline_stage, risk_assessment, tech_stack, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, digital_twins)

    milestones = [
        (1, "MCA Incorporation (CIN U62099MH2025PTC444335) & Team Setup", 3, "2025-04-01", "Verified", "Incorporation certificate verified.", "2025-04-01", "", now),
        (2, "MCA Incorporation (CIN U62099MH2024PTC433392)", 2, "2024-10-10", "Verified", "Incorporated with RoC Mumbai.", "2024-10-10", "", now),
        (2, "Principal Screening & NISM/ARN Registration (₹79,000 Ask)", 4, "2026-12-15", "In Progress", "Compliance roadmap under review.", None, "", now),
        (3, "Incorporation as Genovia Solutions Pvt. Ltd. (CIN U62099MH2025PTC457921)", 3, "2025-09-24", "Verified", "3 student directors verified.", "2025-09-24", "", now),
        (4, "Pre-Incubation Pitch & React Native Prototype", 2, "2025-06-30", "In Progress", "Pitch deck submitted.", None, "", now),
        (5, "Advizy Pre-Incubation Pilot", 3, "2025-12-31", "In Progress", "7 student interns engaged.", None, "", now),
        (6, "Harmocare Validation & 2026-27 Cohort", 3, "2026-12-31", "In Progress", "Active pre-incubation.", None, "", now),
        (7, "MCA Incorporation (CIN U86900MH2025PTC445049) & 2,100+ App Users", 3, "2025-07-30", "Verified", "3 gyms onboarded.", "2025-07-30", "", now),
        (8, "MCA Incorporation (CIN U62011MH2026PTC473470) & Brand Clients", 3, "2026-07-14", "Verified", "Active enterprise clients.", "2026-07-14", "https://www.theaspect.ai/", now),
        (9, "Pre-Incubation Onboarding (2026-27 Odd Sem)", 1, "2026-12-31", "In Progress", "COMPS student team onboarded.", None, "", now)
    ]
    cursor.executemany("INSERT INTO milestones (startup_id, title, phase, target_date, status, verification_notes, completion_date, evidence_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", milestones)

    kpis = [
        (7, "2026-06", 161333.0, 75000.0, 2100, 3, 400.0, 6500.0, "Aligned with Y1 ₹19.36L trajectory.", now),
        (8, "2026-09", 125000.0, 60000.0, 500, 5, 2500.0, 45000.0, "Enterprise clients active.", now),
        (1, "2025-06", 65000.0, 45000.0, 120, 8, 1500.0, 18000.0, "Post-incorporation delivery.", now),
        (3, "2026-09", 50000.0, 35000.0, 300, 10, 1200.0, 15000.0, "Active with 10-member 2026-27 cohort.", now)
    ]
    cursor.executemany("INSERT INTO kpi_records (startup_id, month, revenue, burn_rate, active_users, paying_customers, cac, ltv, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", kpis)

    reviews = [
        (2, "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "2026-11-20", "Pre-Principal Screening & Compliance Audit", "Reviewed ₹79,000 funding ask (₹25k Digio + ₹54k MFD ARN). Confirm NISM status and 30-60-90 day milestones.", 4, "Submit quotations & live demo.", "Completed", now),
        (7, "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "2026-07-20", "2025-26 Incubation Review", "Strong traction (2,100+ users, 20K+ Instagram, 3 gyms).", 5, "Apply for DST/Startup India grants.", "Completed", now),
        (8, "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "2026-09-15", "2026-27 Cohort Onboarding", "Strong enterprise client roster; 3 SAKEC interns approved.", 5, "Track Odd Sem intern deliverables.", "Completed", now)
    ]
    cursor.executemany("INSERT INTO mentorship_sessions (startup_id, mentor_name, mentor_email, session_date, focus_area, feedback, health_rating, action_items, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", reviews)

    conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"SAKEC TBI Render+OneDrive database initialized at {DB_PATH}")
