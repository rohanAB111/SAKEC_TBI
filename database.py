"""
SAKEC Technology Business Incubator (TBI) Platform
Database Module - SQLite Engine & Pre-seeded SAKEC Incubated Startups
Developed by Dr. Rohan Appasaheb Borgalli
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime

DB_PATH = os.environ.get("SAKEC_DB_PATH", "/tmp/sakec_tbi.db")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # High-concurrency performance pragmas for college server scale
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # Users Table (RBAC)
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
        created_at TEXT NOT NULL
    );
    """)

    # Startups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS startups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        tagline TEXT NOT NULL,
        department TEXT NOT NULL,
        founder_name TEXT NOT NULL,
        founder_email TEXT NOT NULL,
        current_phase INTEGER NOT NULL DEFAULT 1, -- 1: Onboarding, 2: Simulation, 3: WorkOS, 4: Mentorship, 5: Investor Readiness
        health_score INTEGER NOT NULL DEFAULT 75, -- 0 to 100
        stage TEXT NOT NULL DEFAULT 'Prototype',
        monthly_burn REAL NOT NULL DEFAULT 50000,
        cash_in_bank REAL NOT NULL DEFAULT 500000,
        runway_months REAL NOT NULL DEFAULT 10,
        monthly_revenue REAL NOT NULL DEFAULT 0,
        customer_count INTEGER NOT NULL DEFAULT 0,
        team_size INTEGER NOT NULL DEFAULT 2,
        investor_readiness_score INTEGER NOT NULL DEFAULT 70,
        pitch_deck_url TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # WorkOS Business Digital Twin Table
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

    # Milestones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        phase INTEGER NOT NULL,
        target_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Completed', 'Verified'
        verification_notes TEXT,
        completion_date TEXT,
        evidence_url TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    # KPI Records (Monthly Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kpi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        month TEXT NOT NULL, -- YYYY-MM
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

    # USim Decision Simulations
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

    # Mentorship Sessions & Reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mentorship_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id INTEGER NOT NULL,
        mentor_name TEXT NOT NULL,
        mentor_email TEXT NOT NULL,
        session_date TEXT NOT NULL,
        focus_area TEXT NOT NULL,
        feedback TEXT NOT NULL,
        health_rating INTEGER NOT NULL DEFAULT 4, -- 1 to 5
        action_items TEXT,
        status TEXT NOT NULL DEFAULT 'Completed',
        created_at TEXT NOT NULL,
        FOREIGN KEY (startup_id) REFERENCES startups(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Check if users already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Seed 5 SAKEC Incubated Startups
    startups = [
        (
            1,
            "CuraDental AI",
            "Deep learning framework for multi-task dental radiograph diagnosis & automated pathology triage",
            "Electronics & Telecommunication (EXTC) & IT",
            "Tanvi Sawant",
            "tanvi.curadental@sakec.ac.in",
            4, # Phase 4: Mentorship & Incubation Monitoring
            93, # Health Score
            "Early Revenue & Clinical Trials",
            85000.0, # Monthly Burn
            1250000.0, # Cash in Bank
            14.7, # Runway Months
            120000.0, # Monthly Revenue
            18, # Customer Count (Clinics/Diagnostic Centers)
            4, # Team size
            88, # Investor Readiness Score
            "https://drive.google.com/curadental_deck.pdf",
            now, now
        ),
        (
            2,
            "EdgeFarm IoT",
            "Solar-powered IoT edge nodes for precision polyhouse microclimate & automated nutrient fertigation",
            "Electronics & Computer Science (ECS)",
            "Aarav Mehta",
            "aarav.edgefarm@sakec.ac.in",
            3, # Phase 3: Operational Deployment through WorkOS
            85,
            "Pilot Validation",
            65000.0,
            680000.0,
            10.5,
            45000.0,
            8, # 8 Farms
            3,
            78,
            "https://drive.google.com/edgefarm_deck.pdf",
            now, now
        ),
        (
            3,
            "EduPulse Analytics",
            "Continuous Outcome-Based Education (OBE) analytics & adaptive student learning diagnostics",
            "Computer Engineering",
            "Neha Kulkarni",
            "neha.edupulse@sakec.ac.in",
            4, # Phase 4: Mentorship & Incubation Monitoring
            89,
            "Early Revenue",
            55000.0,
            750000.0,
            13.6,
            95000.0,
            12, # 12 Academic Departments/Colleges
            4,
            84,
            "https://drive.google.com/edupulse_deck.pdf",
            now, now
        ),
        (
            4,
            "CyberKavach Solutions",
            "Agentless vulnerability intelligence & automated Indian DPDP Act compliance audit engine for MSMEs",
            "Cyber Security",
            "Rishabh Shah",
            "rishabh.cyberkavach@sakec.ac.in",
            2, # Phase 2: Business Simulation & Strategic Planning
            79,
            "MVP Testing",
            40000.0,
            420000.0,
            10.5,
            15000.0,
            5, # 5 MSME beta pilots
            2,
            72,
            "https://drive.google.com/cyberkavach_deck.pdf",
            now, now
        ),
        (
            5,
            "SolarGridIQ",
            "AI edge energy optimization & peer-to-peer campus microgrid storage dispatch",
            "AI & Data Science & EXTC",
            "Kunal Jadhav",
            "kunal.solargrid@sakec.ac.in",
            1, # Phase 1: Startup Selection & Digital Onboarding
            76,
            "Prototype Setup",
            30000.0,
            350000.0,
            11.6,
            0.0,
            1, # Campus pilot
            3,
            68,
            "https://drive.google.com/solargrid_deck.pdf",
            now, now
        )
    ]

    cursor.executemany("""
    INSERT INTO startups (
        id, name, tagline, department, founder_name, founder_email,
        current_phase, health_score, stage, monthly_burn, cash_in_bank,
        runway_months, monthly_revenue, customer_count, team_size,
        investor_readiness_score, pitch_deck_url, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, startups)

    # 2. Seed Users
    users = [
        # Faculty Incharge (Full Admin)
        ("rohan.borgalli", hash_password("Sakec@123"), "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "faculty_incharge", None, "Faculty Incharge - SAKEC TBI", now),
        # College Authorities (Unified Portfolio & Governance View)
        ("principal", hash_password("Sakec@123"), "Dr. Bhavesh Patel", "principal@sakec.ac.in", "authority", None, "Principal - SAKEC", now),
        ("dean.rd", hash_password("Sakec@123"), "Dean Research & Development", "dean.rd@sakec.ac.in", "authority", None, "Dean R&D - SAKEC", now),
        # Mentors
        ("mentor.tech", hash_password("Sakec@123"), "Prof. Milind Khairnar", "milind.khairnar@sakec.ac.in", "mentor", None, "Technical & DeepTech Mentor", now),
        ("mentor.biz", hash_password("Sakec@123"), "Ashwin S. (CybraneX)", "ashwin@cybranex.com", "mentor", None, "Business & Incubation Strategist", now),
        # Startup Founders
        ("founder.curadental", hash_password("Sakec@123"), "Tanvi Sawant", "tanvi.curadental@sakec.ac.in", "founder", 1, "Co-Founder & CEO, CuraDental AI", now),
        ("founder.edgefarm", hash_password("Sakec@123"), "Aarav Mehta", "aarav.edgefarm@sakec.ac.in", "founder", 2, "Founder & CTO, EdgeFarm IoT", now),
        ("founder.edupulse", hash_password("Sakec@123"), "Neha Kulkarni", "neha.edupulse@sakec.ac.in", "founder", 3, "Co-Founder & Lead Dev, EduPulse", now),
        ("founder.cyberkavach", hash_password("Sakec@123"), "Rishabh Shah", "rishabh.cyberkavach@sakec.ac.in", "founder", 4, "Founder & Security Architect, CyberKavach", now),
        ("founder.solargrid", hash_password("Sakec@123"), "Kunal Jadhav", "kunal.solargrid@sakec.ac.in", "founder", 5, "Founder & Embedded Systems Engg, SolarGridIQ", now)
    ]

    cursor.executemany("""
    INSERT INTO users (
        username, password_hash, full_name, email, role, startup_id, designation, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # 3. Seed WorkOS Business Digital Twins
    digital_twins = [
        (
            1,
            json.dumps({"model": "B2B SaaS + Per-Scan API Tier", "pricing": "₹3,500/month base + ₹25 per AI radiograph report", "channels": "Dental Clinics, Maxillofacial Radiology Centers, Hospital Networks"}),
            "28,000+ Dental clinics and diagnostic centers across Western India; Expanding to tier-1 metros.",
            "Instant AI-powered multi-pathology detection (caries, periapical lesions, bone loss) reducing diagnostic turnaround from 24h to 30 seconds with 96.4% precision.",
            json.dumps([
                {"q": "Q1 2026", "item": "CDSCO Software-as-Medical-Device (SaMD) regulatory filing", "status": "Completed"},
                {"q": "Q2 2026", "item": "Multi-center clinical trial validation across 3 dental colleges", "status": "In Progress"},
                {"q": "Q3 2026", "item": "DICOM cloud PACS integration and mobile tablet diagnostic app", "status": "Planned"}
            ]),
            json.dumps([
                {"role": "CEO & Clinical Lead", "name": "Tanvi Sawant", "dept": "EXTC"},
                {"role": "CTO & Deep Learning Architect", "name": "Siddharth Rao", "dept": "IT"},
                {"role": "Faculty Advisor", "name": "Dr. Rohan Appasaheb Borgalli", "dept": "SAKEC TBI"}
            ]),
            "Pilot Conversion Stage: 18 active paying clinics, 34 in trial pipeline",
            "Regulatory clearance delays, radiological liability coverage.",
            "PyTorch, OpenCV, FastAI, FastAPI, PostgreSQL, NVIDIA TensorRT, Docker",
            now
        ),
        (
            2,
            json.dumps({"model": "Hardware Sale + Annual Cloud Telemetry Subscription", "pricing": "₹28,000 per node pack + ₹4,500/year cloud analytics", "channels": "Commercial Polyhouses, Floriculture & Hydroponic Farms in Maharashtra"}),
            "Protected agriculture cultivators, precision greenhouse farmers in Pune-Nashik-Kolhapur belt.",
            "Autonomous LoRaWAN sensor nodes that automatically regulate misting, drip fertigation, and ventilation based on real-time VPD calculations, saving 38% water.",
            json.dumps([
                {"q": "Q1 2026", "item": "PCB fabrication and field testing of Gen-2 solar nodes", "status": "Completed"},
                {"q": "Q2 2026", "item": "Deployment across 8 commercial greenhouses in Nashik", "status": "Completed"},
                {"q": "Q3 2026", "item": "Cellular NB-IoT fallback firmware and multi-zone solenoid valve hub", "status": "In Progress"}
            ]),
            json.dumps([
                {"role": "CTO & Hardware Lead", "name": "Aarav Mehta", "dept": "ECS"},
                {"role": "Embedded Software", "name": "Pooja Desai", "dept": "EXTC"},
                {"role": "Field Agronomist", "name": "V. Jadhav", "dept": "Industry Partner"}
            ]),
            "Demonstration and field trial signups: 8 paying farm installations, 14 leads",
            "Monsoon weatherproofing, sensor calibration drift in high-humidity greenhouses.",
            "ESP32, LoRaWAN, MQTT, Node.js, TimescaleDB, Grafana Dashboard",
            now
        ),
        (
            3,
            json.dumps({"model": "Institutional Campus SaaS (Per Student Annual License)", "pricing": "₹120/student/year or ₹1.8L flat per engineering college department", "channels": "Engineering and Polytechnic colleges undergoing NBA/NAAC accreditation"}),
            "Autonomous and affiliated engineering institutes in Maharashtra and Gujarat.",
            "Eliminates 90% of faculty manual labor in computing direct/indirect CO-PO attainments, course exit surveys, and continuous quality improvement (CQI) reports.",
            json.dumps([
                {"q": "Q1 2026", "item": "AI natural language assessment question paper Bloom's taxonomy classifier", "status": "Completed"},
                {"q": "Q2 2026", "item": "Real-time student diagnostic remedial learning path engine", "status": "Completed"},
                {"q": "Q3 2026", "item": "Integration with standard ERPs (Samarth, Zeenam, TCS iON)", "status": "In Progress"}
            ]),
            json.dumps([
                {"role": "Product & Engineering", "name": "Neha Kulkarni", "dept": "Computer Engg"},
                {"role": "Backend & Cloud Architect", "name": "Aditya Verma", "dept": "IT"},
                {"role": "Accreditation Mentor", "name": "Dr. Rohan Appasaheb Borgalli", "dept": "SAKEC"}
            ]),
            "Institutional pilots: 12 colleges onboarded with active annual agreements",
            "Lengthy academic purchase procurement cycles.",
            "Python, Pandas, SQLite, React, Docker, Openpyxl, Nginx",
            now
        ),
        (
            4,
            json.dumps({"model": "Tiered SaaS Subscription", "pricing": "₹6,999/month for MSME package (up to 50 assets + monthly audit report)", "channels": "Digital agencies, FinTech subcontractors, local healthcare providers"}),
            "SMEs with digital storefronts and customer databases needing compliance with the Digital Personal Data Protection (DPDP) Act 2023.",
            "Zero-installation cloud scanner that crawls attack surfaces, highlights critical misconfigurations, and produces 1-click legal compliance audits.",
            json.dumps([
                {"q": "Q1 2026", "item": "Alpha scanner engine for OWASP Top 10 API vulnerabilities", "status": "Completed"},
                {"q": "Q2 2026", "item": "Automated DPDP Act clause-matching audit reporting generator", "status": "In Progress"},
                {"q": "Q3 2026", "item": "Continuous dark web credential leak alert integration", "status": "Planned"}
            ]),
            json.dumps([
                {"role": "Founder & Security Researcher", "name": "Rishabh Shah", "dept": "Cyber Security"},
                {"role": "Full Stack Dev", "name": "Pranav Shah", "dept": "Computer Engg"}
            ]),
            "Beta testing: 5 SME pilots active, preparing commercial launch in Month 3",
            "False positive rates and legal liabilities in automated vulnerability reporting.",
            "Go, Python, Docker, Nuclei Engine, Elasticsearch, Vue.js",
            now
        ),
        (
            5,
            json.dumps({"model": "Energy Savings Share (ESCO Model) + Hardware Monitoring Fee", "pricing": "15% of verified grid electricity savings + ₹12,000/year gateway support", "channels": "Educational institutes, industrial warehouses, commercial buildings with solar rooftops"}),
            "Commercial establishments in Mumbai Suburban with 50kWp+ solar installations.",
            "Machine learning algorithm that predicts peak solar generation and campus demand 4 hours in advance to optimize battery storage and minimize peak-demand tariff penalties.",
            json.dumps([
                {"q": "Q1 2026", "item": "Baseline energy audit of SAKEC main academic building", "status": "In Progress"},
                {"q": "Q2 2026", "item": "Smart smart-meter RS-485 Modbus telemetry gateway installation", "status": "In Progress"},
                {"q": "Q3 2026", "item": "Predictive battery charge/discharge optimization model deployment", "status": "Planned"}
            ]),
            json.dumps([
                {"role": "Lead Systems Engineer", "name": "Kunal Jadhav", "dept": "EXTC"},
                {"role": "Data Scientist", "name": "Shreya Shetty", "dept": "AI & Data Science"}
            ]),
            "Phase 1 Onboarding: Proof-of-concept installation in SAKEC incubation premises",
            "Grid interconnection utility approvals, high capital expenditure for test batteries.",
            "Python, TensorFlow Lite, Modbus TCP/RTU, Raspberry Pi Compute Module 4, InfluxDB",
            now
        )
    ]

    cursor.executemany("""
    INSERT INTO digital_twins (
        startup_id, business_model, target_market, value_proposition,
        product_roadmap, team_structure, sales_pipeline_stage, risk_assessment,
        tech_stack, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, digital_twins)

    # 4. Seed Milestones aligned with the 5 Incubation Phases from reference document
    milestones = [
        # CuraDental AI (Phase 4)
        (1, "Phase 1: Founder Onboarding & Business Digital Twin Setup", 1, "2026-05-30", "Verified", "All founder accounts, IP declaration and workspace created.", "2026-05-25", "https://sakec.ac.in/tbi/m1", now),
        (1, "Phase 2: USim Unit Economics & Pricing Sensitivity Simulation", 2, "2026-06-30", "Verified", "Detailed cash flow and per-scan margin simulation verified.", "2026-06-28", "https://sakec.ac.in/tbi/m2", now),
        (1, "Phase 3: WorkOS Operational Deployment & Multi-center Clinic Trials", 3, "2026-08-15", "Verified", "18 clinics actively integrated with cloud PACS API.", "2026-08-10", "https://sakec.ac.in/tbi/m3", now),
        (1, "Phase 4: Mentorship Review & Clinical Validation Audit", 4, "2026-09-30", "In Progress", "Review session with technical and clinical mentors underway.", None, None, now),
        (1, "Phase 5: Investor Demo Day & Angel Pitch Deck Finalization", 5, "2026-10-31", "Pending", "Preparing for SAKEC InnoVest 2026 investor forum.", None, None, now),

        # EdgeFarm IoT (Phase 3)
        (2, "Phase 1: Startup Selection & Hardware Prototyping Baseline", 1, "2026-06-15", "Verified", "Onboarded with benchtop sensor telemetry verification.", "2026-06-12", "https://sakec.ac.in/tbi/e1", now),
        (2, "Phase 2: USim Financial Model for Hardware vs Subscription Revenue", 2, "2026-07-15", "Verified", "Simulated BOM margins and 24-month battery replacement cycle.", "2026-07-10", "https://sakec.ac.in/tbi/e2", now),
        (2, "Phase 3: Deployment in 8 Commercial Polyhouses across Maharashtra", 3, "2026-09-20", "In Progress", "6 sites active, 2 under final sensor calibration.", None, None, now),
        (2, "Phase 4: Mentor Operational Audit & Agri-distributor Partnership", 4, "2026-10-15", "Pending", "Pending completion of Phase 3 field validation.", None, None, now),
        (2, "Phase 5: Seed Round Pitching & Scale-up Manufacturing Plan", 5, "2026-11-30", "Pending", "Targeting AgriTech venture accelerators.", None, None, now),

        # EduPulse Analytics (Phase 4)
        (3, "Phase 1: Founder Registration & Platform Architecture Baseline", 1, "2026-05-15", "Verified", "Completed onboarding and data privacy framework.", "2026-05-10", "https://sakec.ac.in/tbi/ed1", now),
        (3, "Phase 2: USim Scenario Modeling for College-wide License Scaling", 2, "2026-06-20", "Verified", "Simulated recurring annual license vs tiered department pricing.", "2026-06-18", "https://sakec.ac.in/tbi/ed2", now),
        (3, "Phase 3: WorkOS Deployment Across 12 Engineering Colleges", 3, "2026-08-01", "Verified", "Successfully handled full academic term exam attainment runs.", "2026-07-28", "https://sakec.ac.in/tbi/ed3", now),
        (3, "Phase 4: Mentor Evaluation & Product Roadmap Extension for NEP 2020", 4, "2026-09-25", "In Progress", "Mentorship review scheduled with academic council experts.", None, None, now),
        (3, "Phase 5: Commercial Scale-up & Institutional Investor Connect", 5, "2026-10-25", "Pending", "Targeting EdTech institutional grant seed funds.", None, None, now),

        # CyberKavach Solutions (Phase 2)
        (4, "Phase 1: Selection, NDA Execution & Lab Workstation Allocation", 1, "2026-07-15", "Verified", "Workstation allocated in SAKEC Cyber Security Lab.", "2026-07-12", "https://sakec.ac.in/tbi/ck1", now),
        (4, "Phase 2: USim Pricing Simulator for MSME Cyber Security Bundles", 2, "2026-09-20", "In Progress", "Running simulations on customer acquisition cost through IT resellers.", None, None, now),
        (4, "Phase 3: WorkOS Setup & 5 Beta Pilots Deployment", 3, "2026-10-20", "Pending", "Beta deployment scheduled for October.", None, None, now),
        (4, "Phase 4: Third-party VAPT Quality Audit & Mentor Signoff", 4, "2026-11-20", "Pending", "Awaiting Phase 3 results.", None, None, now),
        (4, "Phase 5: Investor Readiness & Launch at Cyber Security Summit", 5, "2026-12-20", "Pending", "Targeting pre-seed cybersecurity angel syndicates.", None, None, now),

        # SolarGridIQ (Phase 1)
        (5, "Phase 1: Startup Selection & Digital Onboarding Setup", 1, "2026-09-20", "In Progress", "Founders registered, SAKEC rooftop solar data collection initialized.", None, None, now),
        (5, "Phase 2: USim Energy Arbitrage & Battery Payback Financial Simulation", 2, "2026-10-20", "Pending", "To be executed following sensor data capture.", None, None, now),
        (5, "Phase 3: WorkOS Operational Deployment for Campus Microgrid", 3, "2026-11-20", "Pending", "Awaiting Phase 2 milestones.", None, None, now),
        (5, "Phase 4: Mentor Review with Power Systems Industry Experts", 4, "2026-12-20", "Pending", "Scheduled for Q4.", None, None, now),
        (5, "Phase 5: CleanTech Grant Demonstration & Seed Pitching", 5, "2027-01-20", "Pending", "Targeting DST / BIRAC CleanTech incubation grants.", None, None, now)
    ]

    cursor.executemany("""
    INSERT INTO milestones (
        startup_id, title, phase, target_date, status, verification_notes, completion_date, evidence_url, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, milestones)

    # 5. Seed KPI History Records (for trend graphs)
    kpis = [
        # CuraDental AI (Last 3 months)
        (1, "2026-07", 75000.0, 80000.0, 650, 10, 2400.0, 48000.0, "Beta launch in 10 suburban Mumbai dental clinics.", now),
        (1, "2026-08", 98000.0, 82000.0, 1100, 14, 2100.0, 52000.0, "Expansion to Thane diagnostic centers; AI inference latency reduced to 18s.", now),
        (1, "2026-09", 120000.0, 85000.0, 1550, 18, 1850.0, 56000.0, "Positive operational cash flow milestone achieved; 18 active clinic partners.", now),

        # EdgeFarm IoT
        (2, "2026-07", 20000.0, 60000.0, 80, 3, 4500.0, 35000.0, "First 3 polyhouses deployed in Nashik.", now),
        (2, "2026-08", 32000.0, 62000.0, 140, 5, 4200.0, 38000.0, "Firmware update rolled out with predictive VPD alerting.", now),
        (2, "2026-09", 45000.0, 65000.0, 210, 8, 3800.0, 42000.0, "8 active installations; farmers reported 32% reduction in fertilizer wastage.", now),

        # EduPulse Analytics
        (3, "2026-07", 60000.0, 50000.0, 1800, 6, 3200.0, 65000.0, "Initial pilot departments at University of Mumbai affiliated colleges.", now),
        (3, "2026-08", 80000.0, 52000.0, 3200, 9, 2900.0, 72000.0, "Integrated automated Bloom's taxonomy rubric builder.", now),
        (3, "2026-09", 95000.0, 55000.0, 4600, 12, 2600.0, 78000.0, "12 departments subscribed; preparing for state-wide technical education expo.", now),

        # CyberKavach
        (4, "2026-08", 5000.0, 38000.0, 20, 2, 6000.0, 25000.0, "Alpha prototype test with 2 local logistics companies.", now),
        (4, "2026-09", 15000.0, 40000.0, 65, 5, 5200.0, 30000.0, "5 active paid beta pilots; DPDP Act checklist automated.", now),

        # SolarGridIQ
        (5, "2026-09", 0.0, 30000.0, 10, 1, 0.0, 0.0, "Campus baseline sensor telemetry setup completed.", now)
    ]

    cursor.executemany("""
    INSERT INTO kpi_records (
        startup_id, month, revenue, burn_rate, active_users, paying_customers, cac, ltv, notes, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, kpis)

    # 6. Seed USim Simulations
    sims = [
        (
            1, "Expansion to 50 Diagnostic Hubs", 3500.0, 120000.0, 300.0, 45000.0, 15.0, 3.5, 22.5, 6, 2400000.0,
            "2026-08-20", "Aggressive marketing via dental radiology associations; break-even projected by month 6."
        ),
        (
            2, "Commercial Polyhouse Scaled Model", 28000.0, 95000.0, 14000.0, 35000.0, 12.0, 2.0, 18.2, 8, 1680000.0,
            "2026-07-22", "Hardware margin 50%, recurring telemetry subscriptions provide long-term high LTV."
        ),
        (
            3, "SaaS University License Expansion", 180000.0, 85000.0, 12000.0, 40000.0, 20.0, 4.0, 24.0, 4, 3200000.0,
            "2026-08-15", "Targeting 20 engineering institutes across Western India; high margin software model."
        ),
        (
            4, "MSME Cyber Security Security Compliance Tier", 6999.0, 60000.0, 800.0, 30000.0, 18.0, 5.0, 14.5, 7, 1200000.0,
            "2026-09-05", "Automated cloud scans minimize per-unit marginal costs to under ₹800."
        )
    ]

    cursor.executemany("""
    INSERT INTO simulations (
        startup_id, scenario_name, base_price, monthly_fixed_cost, variable_cost_per_unit,
        marketing_spend, organic_growth_rate, churn_rate, runway_result_months, break_even_month,
        projected_arr, simulation_date, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sims)

    # 7. Seed Mentorship Sessions
    reviews = [
        (
            1, "Prof. Milind Khairnar", "milind.khairnar@sakec.ac.in", "2026-08-28", "Deep Learning Model Latency & Hospital PACS Integration",
            "The model inference speed on TensorRT meets clinical benchmarks (<1 sec). Recommended obtaining CDSCO software classification guidelines before expanding pilot to general hospitals.",
            5, "Finalize ethical committee approvals and document model accuracy on diverse panoramic radiograph datasets.", "Completed", now
        ),
        (
            1, "Ashwin S. (CybraneX)", "ashwin@cybranex.com", "2026-09-08", "Unit Economics & B2B Clinic Pricing Structure",
            "Examined the USim pricing simulation. The tiered per-scan model is viable. Advised offering an upfront annual prepayment discount to extend runway to 18+ months.",
            5, "Prepare pitch deck tailored for healthcare angel investors at SAKEC InnoVest.", "Completed", now
        ),
        (
            2, "Prof. Milind Khairnar", "milind.khairnar@sakec.ac.in", "2026-09-02", "LoRaWAN Gateway Range & Enclosure Weatherproofing",
            "Tested transmission range in polyhouse metallic frame environment. Signal propagation is reliable up to 1.8km. IP67 enclosures must be used for sensors exposed to misting nozzles.",
            4, "Order batch of custom conformal coated PCBs for the next 10 installations.", "Completed", now
        ),
        (
            3, "Dr. Rohan Appasaheb Borgalli", "incubation@sakec.ac.in", "2026-09-10", "NBA/NAAC Accreditation Formula Verification & CQI Workflows",
            "Verified that the calculation matrices strictly comply with NBA Tier-I and Tier-II manuals. The faculty time savings will be the primary selling proposition for academic leaders.",
            5, "Incorporate export templates for NAAC Criterion 2 and NBA Criterion 3.", "Completed", now
        ),
        (
            4, "Ashwin S. (CybraneX)", "ashwin@cybranex.com", "2026-09-12", "Go-To-Market for MSME Regulatory Compliance",
            "Reviewed USim customer acquisition scenarios. Direct enterprise sales are slow; partnering with chartered accountants and legal compliance consultants will drastically reduce CAC.",
            4, "Draft channel partner commission framework for SME audit firms.", "Completed", now
        )
    ]

    cursor.executemany("""
    INSERT INTO mentorship_sessions (
        startup_id, mentor_name, mentor_email, session_date, focus_area, feedback,
        health_rating, action_items, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, reviews)

    conn.commit()

if __name__ == "__main__":
    init_db()
    print(f"Database successfully initialized at {DB_PATH}")
