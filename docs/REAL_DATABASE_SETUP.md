# 🗄️ Setting Up Real PostgreSQL Database on Windows

## 📥 **Step 1: Install PostgreSQL on Windows**

### Download and Install:
1. Go to: https://www.postgresql.org/download/windows/
2. Download PostgreSQL 15 or 16 (latest stable)
3. Run the installer with these settings:
   - **Port**: 5432 (default)
   - **Username**: postgres
   - **Password**: (choose a strong password, e.g., "postgres123")
   - **Database**: postgres (default)

### Verify Installation:
```powershell
# Check if PostgreSQL is running
Get-Service postgresql*

# Or check if port is listening
netstat -an | findstr :5432
```

---

## 🔧 **Step 2: Create Your Financial Database**

### Using pgAdmin (GUI):
1. Open pgAdmin (installed with PostgreSQL)
2. Connect to localhost server
3. Create new database: `financial_trading_db`

### Or using Command Line:
```powershell
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE financial_trading_db;

# Create user for your pipeline
CREATE USER financial_user WITH PASSWORD 'financial123';
GRANT ALL PRIVILEGES ON DATABASE financial_trading_db TO financial_user;
```

---

## 📊 **Step 3: Update Your Pipeline Configuration**

### Update .env file:
```env
# Real PostgreSQL Database (not Docker)
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=financial_trading_db  
DB_USER=financial_user
DB_PASSWORD=financial123

# Or use postgres superuser
DB_USER=postgres
DB_PASSWORD=postgres123  # Your chosen password
```

---

## 🔄 **Step 4: Modified Pipeline for Real Database**

I'll create a version that connects to your local PostgreSQL instead of Docker.

---

## 📍 **Database Location on Your Computer:**

### Windows Installation Locations:
- **Program Files**: `C:\Program Files\PostgreSQL\15\`
- **Data Directory**: `C:\Program Files\PostgreSQL\15\data\`
- **Configuration**: `C:\Program Files\PostgreSQL\15\data\postgresql.conf`
- **Service**: Windows Services → postgresql-x64-15

### Your Data Will Be Stored In:
- **Database Files**: `C:\Program Files\PostgreSQL\15\data\base\`
- **Logs**: `C:\Program Files\PostgreSQL\15\data\log\`
- **Backups**: Custom location you specify

---

## 🎯 **Advantages of Real PostgreSQL:**

✅ **Persistent Data**: Survives computer restarts
✅ **Full Control**: Complete database administration  
✅ **Better Performance**: No container overhead
✅ **Native Tools**: pgAdmin, psql command line
✅ **Backup/Restore**: Standard PostgreSQL tools
✅ **Production-Like**: Same as enterprise deployments

---

## 🚀 **Ready to Install?**

Would you like me to:
1. **Guide you through PostgreSQL installation**
2. **Create a modified pipeline script for real database**
3. **Show you how to migrate existing Docker data**
4. **Set up database backup procedures**

Choose your preferred approach!