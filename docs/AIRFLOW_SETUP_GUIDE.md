# 🚁 Apache Airflow Setup Guide

> Complete guide for setting up and running Apache Airflow with Docker for automated ETL pipeline orchestration

---

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

This project uses **Apache Airflow 2.7.3** running in Docker containers to automate the cryptocurrency data collection, processing, and storage pipeline.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              Airflow Components                      │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Webserver  │  │  Scheduler   │  │ PostgreSQL│ │
│  │  (Port 8080)│  │   (Worker)   │  │    (DB)   │ │
│  └─────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                        │
                        ↓
        ┌───────────────────────────────┐
        │  Financial Crypto ETL DAG     │
        │  (Every 6 hours)              │
        ├───────────────────────────────┤
        │  1. Collect data from APIs    │
        │  2. Verify S3 upload          │
        │  3. Load to Snowflake         │
        │  4. Verify data quality       │
        │  5. Send notification         │
        └───────────────────────────────┘
```

---

## 📦 Prerequisites

### Required Software

- ✅ **Docker Desktop** 20.10+ (with WSL2 on Windows)
- ✅ **Python 3.12+** (for local testing)
- ✅ **Git**

### Required Credentials

- ✅ **AWS Account** (for S3 storage)
  - IAM user with S3 access
  - Access Key ID and Secret Access Key
- ✅ **API Keys**
  - CryptoCompare API key
  - Alpha Vantage API key (optional)
- ✅ **Snowflake Account** (optional for data warehouse)

---

## 🚀 Quick Start

### Step 1: Configure AWS Credentials

Edit the `.env` file in the project root:

```bash
# Open .env file
notepad .env

# Add your AWS credentials:
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
```

⚠️ **Security Note**: The `.env` file is in `.gitignore` and will NOT be committed to git.

### Step 2: Build Custom Airflow Image

```powershell
# Build the custom Docker image with all dependencies
docker-compose -f docker-compose-airflow.yml build

# Expected time: 5-10 minutes (one-time build)
```

The custom image includes:
- Apache Airflow 2.7.3
- boto3, snowflake-connector-python
- pandas, numpy, pyarrow
- All required Python packages

### Step 3: Start Airflow

```powershell
# Start all Airflow services
docker-compose -f docker-compose-airflow.yml up -d

# Check status (wait for all containers to be "healthy")
docker-compose -f docker-compose-airflow.yml ps
```

Services will start in this order:
1. PostgreSQL database (5-10 seconds)
2. Airflow initialization (10-15 seconds)
3. Airflow webserver (15-20 seconds)
4. Airflow scheduler (5-10 seconds)

### Step 4: Access Airflow UI

1. Open browser: http://localhost:8080
2. Login credentials:
   - **Username**: `admin`
   - **Password**: `admin`

3. Find your DAG: `financial_crypto_etl_pipeline`
4. Enable the DAG using the toggle switch

---

## ⚙️ Configuration

### DAG Schedule

The pipeline runs automatically **every 6 hours**:
- Schedule: `0 */6 * * *` (cron expression)
- Times: 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM (UTC)

### Modify Schedule

Edit `dags/crypto_etl_pipeline.py`:

```python
# Change schedule_interval
dag = DAG(
    'financial_crypto_etl_pipeline',
    schedule_interval='0 */6 * * *',  # ← Modify this
    ...
)
```

Common schedules:
- Every hour: `'0 * * * *'`
- Every 4 hours: `'0 */4 * * *'`
- Every day at midnight: `'0 0 * * *'`
- Twice daily: `'0 0,12 * * *'`

### Environment Variables

All configuration is in `.env`:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# Airflow Settings
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin
```

### Volume Mounts

Data persists in these directories:
- `./dags/` - DAG definitions
- `./data/` - Collected data files
- `./airflow_home/logs/` - Task logs
- `./scripts/` - Python scripts
- `./automation/` - Automation scripts

---

## 🏃 Running the Pipeline

### Manual Trigger

1. Go to Airflow UI: http://localhost:8080
2. Find `financial_crypto_etl_pipeline`
3. Click the ▶️ play button
4. Click "Trigger DAG"

### View Task Logs

1. Click on a task square (colored box)
2. Click "Log" button
3. View real-time execution logs

### Monitor Progress

The DAG has 5 tasks:

1. **collect_crypto_data_from_api** (Green = Success)
   - Fetches minute-level crypto data
   - Saves JSON and Parquet files
   - Duration: ~75 seconds

2. **verify_s3_upload** (Green = Success)
   - Checks S3 for uploaded files
   - Validates file existence

3. **load_data_to_snowflake** (Optional)
   - Loads Parquet from S3 to Snowflake
   - Skip if Snowflake not configured

4. **verify_snowflake_data** (Optional)
   - Validates row counts
   - Checks data quality

5. **send_success_notification**
   - Prints completion summary
   - Can be extended for email/Slack

---

## 🔍 Monitoring & Troubleshooting

### Check Container Status

```powershell
# View all containers
docker-compose -f docker-compose-airflow.yml ps

# View logs
docker-compose -f docker-compose-airflow.yml logs -f airflow-scheduler
docker-compose -f docker-compose-airflow.yml logs -f airflow-webserver

# Check specific task logs
docker-compose -f docker-compose-airflow.yml logs airflow-scheduler | Select-String "collect_crypto"
```

### Common Issues

#### 1. WSL Error (Windows)

**Error**: "Docker Desktop is unable to communicate with WSL"

**Solution**:
```powershell
# Restart WSL
wsl --shutdown

# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

#### 2. Container Unhealthy

**Error**: `(unhealthy)` in container status

**Solution**:
```powershell
# Restart specific service
docker-compose -f docker-compose-airflow.yml restart airflow-scheduler

# Or restart all
docker-compose -f docker-compose-airflow.yml restart
```

#### 3. Task Failing with AWS Credentials

**Error**: "NoCredentialsError" or "Unable to locate credentials"

**Solution**:
1. Check `.env` file has correct AWS credentials
2. Restart containers to pick up new environment variables:
   ```powershell
   docker-compose -f docker-compose-airflow.yml restart
   ```

#### 4. DAG Not Appearing

**Solution**:
1. Check DAG file for syntax errors
2. Refresh Airflow UI (F5)
3. Check scheduler logs:
   ```powershell
   docker-compose -f docker-compose-airflow.yml logs airflow-scheduler | Select-String "ERROR"
   ```

### View Collected Data

```powershell
# List files in data directory
Get-ChildItem -Path "data" -Filter "crypto_minute_data_*.json"

# View files inside Docker container
docker exec airflow-scheduler-1 ls -lh /opt/airflow/data/
```

---

## 🔐 Security Best Practices

### 1. Never Commit Credentials

✅ **DO**:
- Use `.env` file for credentials (already in `.gitignore`)
- Use environment variables in docker-compose
- Keep `.env` file secure and private

❌ **DON'T**:
- Put credentials in `docker-compose.yml`
- Commit `.env` to git
- Share `.env` file publicly
- Hard-code credentials in Python files

### 2. AWS IAM Best Practices

Create a dedicated IAM user for this project:

**Minimal IAM Policy** (S3 access only):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::financial-trading-data-lake",
        "arn:aws:s3:::financial-trading-data-lake/*"
      ]
    }
  ]
}
```

### 3. Rotate Credentials Regularly

```bash
# Update AWS credentials in .env
AWS_ACCESS_KEY_ID=new_key
AWS_SECRET_ACCESS_KEY=new_secret

# Restart Airflow
docker-compose -f docker-compose-airflow.yml restart
```

### 4. Use IAM Roles in Production

When deploying to AWS (EC2, ECS, EKS), use IAM roles instead of access keys:

```yaml
# docker-compose-airflow.yml (Production)
environment:
  # Remove these lines - use IAM role instead
  # AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  # AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
  AWS_DEFAULT_REGION: us-east-1
```

---

## 🛠️ Advanced Configuration

### Custom Docker Image

To add more Python packages, edit `requirements-airflow.txt`:

```text
# Add your packages
my-package==1.0.0

# Rebuild image
docker-compose -f docker-compose-airflow.yml build
```

### Change Airflow Executor

For parallel task execution, use Celery Executor:

```yaml
# docker-compose-airflow.yml
environment:
  AIRFLOW__CORE__EXECUTOR: CeleryExecutor
```

### Enable Email Notifications

Edit `dags/crypto_etl_pipeline.py`:

```python
default_args = {
    'email': ['your-email@example.com'],
    'email_on_failure': True,  # Enable
    'email_on_retry': True,
}
```

Configure SMTP in docker-compose:
```yaml
environment:
  AIRFLOW__SMTP__SMTP_HOST: smtp.gmail.com
  AIRFLOW__SMTP__SMTP_PORT: 587
  AIRFLOW__SMTP__SMTP_USER: your-email@gmail.com
  AIRFLOW__SMTP__SMTP_PASSWORD: your-app-password
  AIRFLOW__SMTP__SMTP_MAIL_FROM: airflow@example.com
```

---

## 📊 Production Deployment

### For Production Use:

1. **Use IAM Roles** (not access keys)
2. **External PostgreSQL** (not Docker container)
3. **Load Balancer** for webserver
4. **Auto-scaling** for workers
5. **External Logging** (CloudWatch, DataDog)
6. **Monitoring** (Prometheus, Grafana)
7. **Secrets Manager** (AWS Secrets Manager, HashiCorp Vault)

### Recommended AWS Services:

- **AWS MWAA** (Managed Workflows for Apache Airflow)
- **Amazon ECS** with Fargate
- **Amazon EKS** with Kubernetes

---

## 🆘 Getting Help

### Resources

- **Airflow UI**: http://localhost:8080
- **Airflow Documentation**: https://airflow.apache.org/docs/
- **Project Documentation**: `docs/` folder
- **GitHub Issues**: https://github.com/tchamna/financial-trading-etl-pipeline/issues

### Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review this guide
3. Check Airflow UI for task details
4. Open a GitHub issue
5. Email: tchamna@gmail.com

---

## 🎉 Success Checklist

- ✅ Docker Desktop running
- ✅ `.env` file configured with AWS credentials
- ✅ Custom Airflow image built successfully
- ✅ All containers healthy and running
- ✅ Airflow UI accessible at http://localhost:8080
- ✅ DAG enabled and visible in UI
- ✅ First manual run successful
- ✅ Data files created in `data/` directory
- ✅ S3 upload verified (if AWS configured)

---

<div align="center">

**🚀 Your Airflow ETL Pipeline is Ready!**

Made with ❤️ by Shck Tchamna

</div>
