# 🔐 DATABASE CREDENTIALS & CONNECTIONS

## 📋 Summary Table

| Service | Host | Port | Database | User | Password | Purpose |
|---------|------|------|----------|------|----------|---------|
| **Application DB** | devom.silog.co.id | 5432 | devom.silog.co.id | om | om | Source OLTP data |
| **Application DB** | 172.20.145.83 | 5432 | devom.silog.co.id | om | om | Alternative IP |
| **Airflow DB** | postgres (Docker) | 5432 | airflow | airflow | airflow | Analytics & metadata |
| **Airflow DB** | localhost | 5432 | airflow | airflow | airflow | From host machine |

---

## 📊 Database Roles

### Source Database (devom.silog.co.id)
**OLTP - Production Database**

User: `om` / `om`

Tables (OLTP Schema):
- `public.driver_armada` - Master data drivers
- `public.rating` - Driver ratings & reviews
- `public.delivery_order` - Delivery records
- `public.perangkat_gps_driver` - GPS device info
- `public.rekening_driver` - Bank account records
- `public.log_perjalanan_armada` - Journey logs (optional)
- `public.log_aktifitas_driver` - Activity logs (optional)

### Target Database (Airflow Local)
**Analytics & ETL**

User: `airflow` / `airflow`

Schemas:
- `public.*` - OLTP replicated data (temporary)
- `analytics.fact_driver_performance` - KPI metrics

---

## 🔗 Airflow Connections

### Connection 1: postgres_default
**For Airflow metadata**
```
Type: PostgreSQL
Host: postgres (Docker) / localhost (Host)
Database: airflow
User: airflow
Password: airflow
Port: 5432
```

### Connection 2: postgres_app
**For Application Database** (reference only - Docker can't access)
```
Type: PostgreSQL
Host: devom.silog.co.id
Database: devom.silog.co.id
User: om
Password: om
Port: 5432
```

---

## 🐳 Docker Container Details

### PostgreSQL Container
```bash
Container Name: postgres
Image: postgres:18
Port: 5432
Environment:
  - POSTGRES_USER=airflow
  - POSTGRES_PASSWORD=airflow
  - POSTGRES_DB=airflow
```

Access:
```bash
docker exec postgres psql -U airflow -d airflow
```

### Airflow Services
```bash
# Webserver
docker exec airflow-webserver bash

# Scheduler
docker exec airflow-scheduler bash

# Worker
docker exec airflow-worker bash
```

---

## 🛠️ Connection Test Commands

### Test from Host Machine
```bash
# Install psycopg2 first
pip3 install psycopg2-binary

# Test Airflow DB
python3 << 'EOF'
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='airflow',
        user='airflow',
        password='airflow',
        port=5432
    )
    print('✅ Connected to Airflow DB')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    print(cursor.fetchone())
    conn.close()
except Exception as e:
    print(f'❌ {str(e)}')
EOF

# Test Application DB (might fail due to network)
python3 << 'EOF'
import psycopg2
try:
    conn = psycopg2.connect(
        host='devom.silog.co.id',
        database='devom.silog.co.id',
        user='om',
        password='om',
        port=5432
    )
    print('✅ Connected to Application DB')
    conn.close()
except Exception as e:
    print(f'❌ {str(e)}')
EOF
```

### Test from Docker Container
```bash
# Airflow container
docker exec airflow-webserver python3 << 'EOF'
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='airflow',
    user='airflow',
    password='airflow'
)
print('✅ Airflow DB OK')
conn.close()
EOF

# Direct psql
docker exec postgres psql -U airflow -d airflow -c "SELECT COUNT(*) FROM driver_armada;"
```

---

## 📁 CSV Import Folder

**Location:** `/home/rafiez/airflow-stack/data/`

**Expected files:**
```
driver_armada.csv
rating.csv
delivery_order.csv
perangkat_gps_driver.csv
rekening_driver.csv
```

---

## 🔄 Data Flow Summary

```
1. Source (devom.silog.co.id)
   └─ Export via pgAdmin4
   
2. CSV Files
   └─ /home/rafiez/airflow-stack/data/

3. Import to Airflow
   └─ public.driver_armada
   └─ public.rating
   └─ public.delivery_order
   └─ public.perangkat_gps_driver
   └─ public.rekening_driver

4. ETL Transform
   └─ 5-table JOIN
   └─ Calculate metrics
   └─ Weighted KPI

5. Analytics
   └─ analytics.fact_driver_performance
   └─ Ready for dashboards
```

---

## 💾 Backup & Recovery

### Backup PostgreSQL
```bash
docker exec postgres pg_dump -U airflow -d airflow > /backup/airflow_backup.sql
```

### Restore PostgreSQL
```bash
docker exec -i postgres psql -U airflow -d airflow < /backup/airflow_backup.sql
```

### Backup CSV Files
```bash
tar -czf /backup/csv_backup.tar.gz /home/rafiez/airflow-stack/data/
```

---

## 🔐 Security Notes

**Production Recommendations:**
- Never hardcode passwords in scripts
- Use `.env` files for credentials
- Rotate passwords regularly
- Use environment variables in Docker

**For this setup:**
- All credentials are development/local
- Update before production deployment
- Use Airflow Secrets Manager for sensitive data

---

## 📞 References

- **pgAdmin4:** http://localhost:5050
- **Airflow:** http://localhost:8080
- **PostgreSQL Client:** `psql`
- **Docker:** `docker exec`

---

**Last Updated:** January 13, 2026
