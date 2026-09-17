# SAKEC Technology Business Incubator (TBI) Management Platform
### Developed by Dr. Rohan Appasaheb Borgalli
*Faculty Incharge, Technology Business Incubator (TBI)*  
*Shah & Anchor Kutchhi Engineering College (SAKEC), Chembur, Mumbai*

---

## Overview

The **SAKEC TBI Platform** is a specialized web application engineered for the **SAKEC Technology Business Incubator (TBI)**. It provides an end-to-end management, simulation, and progress-tracking environment for faculty leadership, college authorities, startup founders, and industry mentors.

Built in direct accordance with the **CybraneX USim + WorkOS Incubation Platform** specifications, the system translates strategic business simulation, operational digital twins, and structured milestone governance into a lightweight, high-performance, self-hosted web application deployable directly on college servers.

## Key Capabilities

1. **Unified Portfolio Dashboard for Authorities**: Instant visibility into aggregate portfolio metrics, active ventures, monthly revenues, health scores, cash burn, and institutional NAAC/NIRF/NBA innovation indicators.
2. **WorkOS Business Digital Twin**: 360-degree company representation encompassing business models, target markets, tech stack, product roadmaps, and risk assessments.
3. **USim Startup Decision Simulator**: Interactive financial modeling tool calculating unit economics, contribution margin, CAC, LTV, break-even months, and 12-month runway projections.
4. **Milestones & KPI Progress Tracker**: Phase 1 through Phase 5 milestone tracking with founder submission and faculty verification workflows.
5. **Mentorship & Evaluation Hub**: Structured review logging, 5-star rating audits, and action item tracking.
6. **Scalability**: Pre-seeded with SAKEC's 5 inaugural startups, with 1-click provisioning for unlimited future startups.

## Quick Start

```bash
# 1. Initialize SQLite Database
python3 database.py

# 2. Start Application Server
python3 server.py
```
Open your browser at `http://localhost:8080`.

For production deployment instructions on the SAKEC college server, see [DEPLOYMENT.md](DEPLOYMENT.md).
