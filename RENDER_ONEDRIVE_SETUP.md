# SAKEC TBI Platform — Render.com + OneDrive (`incubation@sakec.ac.in`) Deployment Guide
### Developed by Dr. Rohan Appasaheb Borgalli

---

## 1. Deploy on Render.com (Public HTTPS Access)
1. Push all files from `sakec_tbi_platform/` to your GitHub repo (`https://github.com/rohanAB111/SAKEC_TBI`) so `server.py`, `database.py`, `requirements.txt`, `render.yaml`, and the `static/` folder are at the root.
2. Open [Render Dashboard](https://dashboard.render.com/) → **New +** → **Web Service** (or update your existing `sakec-tbi` service):
   - **Region:** Singapore
   - **Build Command:** `python3 database.py`
   - **Start Command:** `python3 server.py`
   - **Environment Variables:**
     - `SAKEC_DB_PATH` = `/tmp/sakec_tbi.db`
     - `ONEDRIVE_UPLOAD_URL` = *(paste your `incubation@sakec.ac.in` OneDrive File Request / Shared Folder link — you can also change this anytime inside the Admin tab!)*
3. Click **Deploy**. Your platform will be live over HTTPS at `https://sakec-tbi.onrender.com`.

---

## 2. Link Your `incubation@sakec.ac.in` OneDrive (5-Minute Setup)
To let founders upload documents directly into your `incubation@sakec.ac.in` OneDrive **without sharing your OneDrive password**:
1. Sign in to **OneDrive for Business** with **`incubation@sakec.ac.in`**.
2. Create a folder named **`SAKEC_TBI_Startup_Documents`** (with subfolders `2024-25`, `2025-26`, `2026-27`, or one folder per startup).
3. Select the folder → click **Request files** (in OneDrive for Business) or **Share** → **Anyone with the link can upload/edit**.
4. Copy the generated OneDrive link.
5. Log into the SAKEC TBI Portal as **`rohan.borgalli`** → go to **🚀 Admin, Accounts & OneDrive** → paste the link into **Master `incubation@sakec.ac.in` OneDrive Upload URL** and click **Save Settings**.
   - You can also assign a startup-specific OneDrive folder link per startup when onboarding or editing a startup!

---

## 3. Ongoing Admin Workflow
- **Create Accounts for Each Admin:** Go to **🚀 Admin, Accounts & OneDrive** → **Create New Admin / User Account** to issue individual logins for co-coordinators, department admins, Principal, Dean R&D, mentors, or founders.
- **Add New Startups / Pre-Incubation Ventures:** Fill out the onboarding form, choose `Incubated (Pvt. Ltd.)` or `Pre-Incubation`, enter a **Founder Username & Password**, and click Onboard. The portal automatically creates the founder's login and provisions their **8-item Required Documents Checklist**.
- **Download Year-Wise Official Reports:** From the top bar or Portfolio tab, select `2024-25`, `2025-26`, `2026-27`, or `All Years`, and click **🖨️ Official Year-Wise Report (PDF/Print)** to download/print the formal institutional report with separate **Incubated (Pvt. Ltd.)** and **Pre-Incubation** tables, CIN/DIN, Interns Roster, and Principal/Faculty Incharge signature blocks.
- **Database Backup (Render Free Tier Tip):** Click **💾 Download Full JSON Backup** in the Admin tab after major updates so you always have a local backup of any newly added startups and accounts.
