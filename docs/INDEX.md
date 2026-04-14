# 📚 Documentation Index

**Quick navigation guide for all Airflow Stack documentation**

---

## 🎯 Where To Start?

| Your Role | Start Here | Then Read |
|-----------|-----------|-----------|
| **New User** | [Main README](../README.md) | [Installation Guide](INSTALLATION.md) |
| **Admin/DevOps** | [Installation Guide](INSTALLATION.md) | [Architecture](ARCHITECTURE.md) → [Troubleshooting](TROUBLESHOOTING.md) |
| **Data Analyst** | [Main README](../README.md) | [DAGs Reference](DAGS.md) → [Database Schema](DATABASE_SCHEMA.md) |
| **Developer** | [Architecture](ARCHITECTURE.md) | [DAGs Reference](DAGS.md) → [Database Schema](DATABASE_SCHEMA.md) |

---

## 📖 All Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [README.md](../README.md) | Project overview & 5-min quick start | 5-10 min |
| [INSTALLATION.md](INSTALLATION.md) | Step-by-step setup guide | 15-20 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design & data flows | 10-15 min |
| [DAGS.md](DAGS.md) | All 3 DAGs explained | 15-20 min |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Tables & relationships | 10-15 min |
| [DASHBOARDS.md](DASHBOARDS.md) | Analytics tools (Metabase, Grafana, Superset) | 15-20 min |
| [SCRIPTS.md](SCRIPTS.md) | Helper scripts reference | 10-15 min |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues & solutions | Reference |

---

## 🔍 Find Answer By Topic

### Getting Started
- **Q: How do I set up Airflow Stack?**  
  → [Installation Guide](INSTALLATION.md)

- **Q: What's included and how does it work?**  
  → [Main README](../README.md) + [Architecture](ARCHITECTURE.md)

- **Q: What are the system requirements?**  
  → [Main README - Requirements](../README.md#-system-requirements)

### Understanding The Data

- **Q: What DAGs do we have and what do they do?**  
  → [DAGs Reference](DAGS.md)

- **Q: What tables exist and what data do they contain?**  
  → [Database Schema](DATABASE_SCHEMA.md)

- **Q: How often is data updated?**  
  → [DAGs Reference - Schedules](DAGS.md#-schedules)

- **Q: Where does data come from?**  
  → [Architecture - Data Sources](ARCHITECTURE.md)

### Analytics & Dashboards

- **Q: How do I create a Metabase dashboard?**  
  → [Dashboards - Metabase](DASHBOARDS.md#metabase-port-3000)

- **Q: Which tool should I use for analytics?**  
  → [Dashboards - Tool Comparison](DASHBOARDS.md#tool-comparison)

- **Q: How do I write SQL queries?**  
  → [Database Schema - Sample Queries](DATABASE_SCHEMA.md)

### Troubleshooting

- **Q: The DAG is not running. What's wrong?**  
  → [Troubleshooting - DAG Issues](TROUBLESHOOTING.md#dag--airflow-issues)

- **Q: I can't connect to the database.**  
  → [Troubleshooting - Connection Issues](TROUBLESHOOTING.md#connection-issues)

- **Q: Weather data is not updating.**  
  → [Troubleshooting - Data Quality Issues](TROUBLESHOOTING.md#data-quality-issues)

- **Q: Performance is slow. What can I do?**  
  → [Troubleshooting - Performance](TROUBLESHOOTING.md#performance-issues)

### Using Helper Scripts

- **Q: How do I start the system?**  
  → [SCRIPTS - quick_start.sh](SCRIPTS.md)

- **Q: How do I update tables from DEVOM?**  
  → [SCRIPTS - sync_tables_from_devom.sh](SCRIPTS.md)

- **Q: How do I set up Metabase?**  
  → [SCRIPTS - start_metabase.sh](SCRIPTS.md) or [DASHBOARDS](DASHBOARDS.md)

---

## 📚 Learning Paths

### Path 1: System Administrator

```
1. Installation Guide
   └─ Set up infrastructure
2. Architecture Guide
   └─ Understand system design
3. DAGs Reference
   └─ Learn about data pipelines
4. Troubleshooting
   └─ Know how to debug issues
5. Scripts Reference
   └─ Know utility scripts
```

**Estimated Time:** 60 minutes

### Path 2: Data Analyst

```
1. Main README
   └─ Understand project scope
2. DAGs Reference
   └─ Learn data update schedules
3. Database Schema
   └─ Understand available tables
4. Dashboards Setup
   └─ Set up Metabase/Grafana
5. Troubleshooting
   └─ Reference when needed
```

**Estimated Time:** 45 minutes

### Path 3: Data Engineer / Developer

```
1. Installation Guide
   └─ Complete setup
2. Architecture Guide
   └─ Deep dive into design
3. DAGs Reference
   └─ Learn DAG structure
4. Database Schema
   └─ Understand data model
5. Scripts Reference
   └─ Know automation tools
6. Troubleshooting
   └─ Debugging techniques
```

**Estimated Time:** 75 minutes

---

## 🎓 Task Checklists

### First-Time Setup Checklist

- [ ] Read: [Main README](../README.md) - Project overview
- [ ] Install: Docker & Docker Compose
- [ ] Run: `bash scripts/utils/quick_start.sh`
- [ ] Run: `bash scripts/setup/setup_warehouse_db.sh`
- [ ] Run: `bash scripts/etl/copy_devom_structure.sh`
- [ ] Verify: Airflow UI shows DAGs (http://localhost:8080)
- [ ] Read: [DAGs Reference](DAGS.md)

### Daily Operations

- [ ] Check: All containers running - `docker ps`
- [ ] Check: Airflow UI (http://localhost:8080) - DAGs scheduled?
- [ ] Check: Any failed DAG runs?
- [ ] If issues → Check: [Troubleshooting](TROUBLESHOOTING.md)

### Creating Analytics Dashboard

- [ ] Read: [Database Schema](DATABASE_SCHEMA.md) - Find your tables
- [ ] Read: [Dashboards](DASHBOARDS.md) - Choose tool (Metabase/Grafana/Superset)
- [ ] Follow: Setup steps for your chosen tool
- [ ] Test: Write SQL query first
- [ ] Create: Dashboard using sample queries

### Troubleshooting Problem

- [ ] Search: Find your error in [Troubleshooting Index](TROUBLESHOOTING.md)
- [ ] Follow: Suggested solution steps
- [ ] Check: Relevant logs - Airflow/Docker/Database
- [ ] Test: Fix worked?
- [ ] If not working → Document issue and ask team

---

## 📋 Document Structure

### README.md
**Location:** Root  
**Purpose:** Project entry point with quick start  
**Contains:** Overview, quick start, 5-minute setup, architecture, FAQ

### INSTALLATION.md
**Location:** docs/  
**Purpose:** Complete setup from scratch  
**Contains:** Prerequisites, step-by-step setup, database config, first DAG run

### ARCHITECTURE.md
**Location:** docs/  
**Purpose:** System design & components  
**Contains:** Architecture diagram, data flows, tech stack, integrations

### DAGS.md
**Location:** docs/  
**Purpose:** Data pipeline reference  
**Contains:** All 3 DAGs explained, tasks, scheduling, monitoring, error handling

### DATABASE_SCHEMA.md
**Location:** docs/  
**Purpose:** Database structure reference  
**Contains:** Schemas, tables (90+), relationships, sample queries

### DASHBOARDS.md
**Location:** docs/  
**Purpose:** Analytics tools setup  
**Contains:** Metabase, Grafana, Superset setup, sample queries, tool comparison

### SCRIPTS.md
**Location:** docs/  
**Purpose:** Helper scripts reference  
**Contains:** 22 scripts, usage, dependencies, troubleshooting

### TROUBLESHOOTING.md
**Location:** docs/  
**Purpose:** Common issues & solutions  
**Contains:** Connection issues, DB problems, DAG issues, performance fixes

---

## 🔗 Cross-Reference Map

```
README.md (Main Entry)
├── → Installation Guide (setup)
├── → Architecture (how it works)
├── → DAGs Reference (pipelines)
├── → Database Schema (data)
└── → Dashboards (analytics)

Each documentation page:
├── → Related documents (in text)
├── → Troubleshooting (when stuck)
├── → Scripts Reference (how-to)
└── → Back to README or Index
```

---

## 💡 Tips for Effective Documentation Use

### Reading Efficiently
- **Skim headers first** - Get overview before reading details
- **Use table of contents** - Jump directly to your topic
- **Search with Ctrl+F** - Find keywords quickly
- **Follow "Related" links** - Navigate between topics

### Finding Information Fast
1. **Use this index first** - Find document by problem
2. **Check Troubleshooting** - Most common answers are there
3. **Look for examples** - Often clearer than explanations
4. **Review related documents** - For complete picture

### When Stuck
1. Search [Troubleshooting](TROUBLESHOOTING.md)
2. Check relevant document (e.g., DAGs for DAG issues)
3. Review script logs: `docker-compose logs <service>`
4. Check database logs: `psql` + sample queries
5. Ask team with log excerpts

---

## 📞 Support Resources

### Quick Diagnostic Commands

```bash
# System status
docker-compose ps

# View logs
docker-compose logs airflow-scheduler | tail -50

# Database query
psql -h localhost -U postgres -d warehouse -p 5433

# Airflow UI
# http://localhost:8080
```

### Documentation Search Tips

- **By Error Message:** Search [Troubleshooting](TROUBLESHOOTING.md)
- **By Component:** Search specific document (DAGS, Dashboards, etc.)
- **By Keyword:** Use browser Find (Ctrl+F)
- **By Topic:** Use this index

---

## 📊 Documentation Statistics

| Metric | Count |
|--------|-------|
| **Total Documents** | 8 pages |
| **Total Words** | ~25,000 |
| **Code Examples** | 50+ |
| **Sample Queries** | 30+ |
| **Troubleshooting Sections** | 25+ |
| **Tables Listed** | 90+ |

---

**Last Updated:** April 2026  
**Current Version:** 1.0  
**Status:** Complete ✅

👈 **Back to:** [Main README](../README.md)
