# 🚀 Apache Airflow Setup Guide for Financial ETL Pipeline

## What is Apache Airflow?

Apache Airflow is a platform to **programmatically author, schedule, and monitor workflows**. It's perfect for orchestrating complex data pipelines like ours!

### Key Concepts:
- **DAG (Directed Acyclic Graph)**: Your workflow definition
- **Task**: A single unit of work (e.g., "collect data")
- **Operator**: Defines what a task does (PythonOperator, BashOperator)
- **Scheduler**: Triggers DAGs based on their schedule
- **Webserver**: Provides the UI to monitor and manage DAGs

---

## 📦 Installation Steps

### 1. Run the Setup Script

```powershell
# This will install Airflow and configure everything
python setup_airflow.py
```

**What it does:**
- Installs Apache Airflow 2.7.3
- Initializes the Airflow database
- Creates admin user (username: `admin`, password: `admin`)
- Sets up DAGs folder
- Creates startup scripts

**Installation time:** ~5-10 minutes

---

## 🎯 Starting Airflow

You need **TWO terminals** running simultaneously:

### Terminal 1: Start Webserver
```powershell
# Open PowerShell in project directory
powershell -File start_airflow_webserver.ps1
```

Wait until you see: `Listening at: http://0.0.0.0:8080`

### Terminal 2: Start Scheduler
```powershell
# Open another PowerShell window
powershell -File start_airflow_scheduler.ps1
```

Wait until you see: `Starting the scheduler`

---

## 🌐 Access Airflow UI

1. Open browser: **http://localhost:8080**
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin`

---

## 📊 Your DAG: `financial_crypto_etl_pipeline`

### Pipeline Flow:
```
collect_crypto_data_from_api
          ↓
    verify_s3_upload
          ↓
  load_data_to_snowflake
          ↓
   verify_snowflake_data
          ↓
  send_success_notification
```

### Schedule:
- **Frequency**: Every 6 hours (0:00, 6:00, 12:00, 18:00)
- **First Run**: 5 minutes after you enable the DAG
- **Catchup**: Disabled (won't backfill old runs)

---

## ✅ Enable Your DAG

1. Go to Airflow UI (http://localhost:8080)
2. Find **"financial_crypto_etl_pipeline"** in the DAGs list
3. Click the **toggle switch** on the left to enable it
4. The DAG will automatically start in 5 minutes!

---

## 📱 Using the Airflow UI

### Main Dashboard
- **DAGs List**: All your workflows
- **Toggle**: Enable/disable DAGs
- **Last Run**: Status of the most recent execution
- **Schedule**: When the DAG runs next

### DAG View (click on DAG name)
- **Graph View**: Visual representation of tasks
- **Tree View**: Historical runs with task status
- **Calendar View**: Daily run success/failure
- **Code**: View the DAG Python code

### Task Instance
Click on any task box to:
- **View Logs**: Detailed execution logs
- **XCom**: Data passed between tasks
- **Mark Success/Failed**: Manual status override
- **Clear**: Rerun this task

### Useful Features
- **🔄 Trigger DAG**: Manually start a run (don't wait for schedule)
- **⏸️ Pause/Unpause**: Temporarily disable scheduling
- **🗑️ Delete**: Remove DAG runs from history

---

## 🎨 Task Colors in UI

- **🟢 Dark Green**: Task succeeded
- **🟡 Yellow**: Task is running
- **🔴 Red**: Task failed
- **⚪ White**: Task not started yet
- **🟠 Orange**: Task upstream failed (skipped)
- **🟣 Purple**: Task is queued

---

## 🔍 Monitoring Your Pipeline

### Check DAG Status
1. Go to DAG view
2. Click **Tree View** to see all runs
3. Green boxes = success, Red = failed

### View Task Logs
1. Click on any task box in Graph/Tree view
2. Click **"Log"** button
3. See detailed execution output

### Check Task Output (XCom)
1. Click on task instance
2. Go to **"XCom"** tab
3. View data returned by the task

---

## 🐛 Troubleshooting

### DAG Not Showing Up?
```powershell
# Check if DAG file has errors
python dags/crypto_etl_pipeline.py
```

### Task Failed?
1. Click on the red task box
2. Click **"Log"** to see error message
3. Fix the issue in your code
4. Click **"Clear"** to retry the task

### Scheduler Not Running?
```powershell
# Check scheduler process
Get-Process | Where-Object {$_.ProcessName -like "*airflow*"}
```

### Can't Access UI?
- Make sure webserver is running on port 8080
- Check if another application is using port 8080
- Try: http://127.0.0.1:8080 instead

---

## ⚙️ Configuration

### Airflow Configuration File
Location: `airflow_home/airflow.cfg`

**Key settings to know:**
```ini
[core]
dags_folder = /path/to/dags        # Where DAGs are stored
load_examples = False               # Disable example DAGs

[webserver]
web_server_port = 8080             # UI port

[scheduler]
catchup_by_default = False         # Don't backfill by default
```

---

## 🎓 Learning Resources

### Official Documentation
- **Airflow Docs**: https://airflow.apache.org/docs/
- **Concepts**: https://airflow.apache.org/docs/apache-airflow/stable/concepts/
- **Tutorial**: https://airflow.apache.org/docs/apache-airflow/stable/tutorial/

### Key Topics to Learn
1. **Operators**: PythonOperator, BashOperator, EmailOperator
2. **XCom**: Passing data between tasks
3. **Connections**: Store credentials securely
4. **Variables**: Store configuration
5. **Task Dependencies**: `>>`, `<<`, `set_upstream`, `set_downstream`

---

## 🚀 Advanced Features (To Explore)

### Parallel Execution
```python
# Run multiple tasks in parallel
task1 >> [task2, task3, task4] >> task5
```

### Conditional Tasks
```python
from airflow.operators.python import BranchPythonOperator
# Execute different paths based on conditions
```

### Sensors
```python
from airflow.sensors.filesystem import FileSensor
# Wait for specific conditions before proceeding
```

### Email Alerts
```python
'email': ['your@email.com'],
'email_on_failure': True,
'email_on_retry': True,
```

---

## 📝 Your Pipeline Tasks Explained

### Task 1: `collect_crypto_data_from_api`
- Runs `automation/daily_data_collection.py`
- Collects cryptocurrency data from CryptoCompare API
- Saves to local JSON and uploads to S3 as Parquet

### Task 2: `verify_s3_upload`
- Connects to S3 using boto3
- Verifies files were uploaded successfully
- Counts uploaded files

### Task 3: `load_data_to_snowflake`
- Runs `load_s3_parquet_to_snowflake.py`
- Downloads Parquet files from S3
- Bulk inserts into Snowflake

### Task 4: `verify_snowflake_data`
- Connects to Snowflake
- Checks row counts and data quality
- Verifies latest timestamp

### Task 5: `send_success_notification`
- Prints success message to logs
- Can be extended to send emails/Slack messages

---

## 🔧 Customizing Your Pipeline

### Change Schedule
In `dags/crypto_etl_pipeline.py`:
```python
schedule_interval='0 */6 * * *',  # Every 6 hours
# Change to:
# '0 0 * * *'   # Daily at midnight
# '*/30 * * * *' # Every 30 minutes
# '@hourly'      # Every hour
```

### Add Email Alerts
```python
default_args = {
    'email': ['your@email.com'],
    'email_on_failure': True,
    'email_on_success': False,
}
```

### Add More Tasks
```python
task_new = PythonOperator(
    task_id='my_new_task',
    python_callable=my_function,
    dag=dag,
)

# Add to pipeline
task_collect_data >> task_new >> task_verify_s3
```

---

## 🎯 Quick Start Checklist

- [ ] Run `python setup_airflow.py`
- [ ] Start webserver: `powershell -File start_airflow_webserver.ps1`
- [ ] Start scheduler: `powershell -File start_airflow_scheduler.ps1`
- [ ] Access UI: http://localhost:8080
- [ ] Login with admin/admin
- [ ] Enable `financial_crypto_etl_pipeline` DAG
- [ ] Wait 5 minutes for first run
- [ ] Monitor in Tree View
- [ ] Check task logs

---

## 📞 Support

If you encounter issues:
1. Check task logs in Airflow UI
2. Review Airflow scheduler terminal output
3. Check `airflow_home/logs` directory
4. Run DAG file manually: `python dags/crypto_etl_pipeline.py`

---

**Happy Learning! 🎓**

You're now using industry-standard workflow orchestration! This is the same tool used by:
- Airbnb (created Airflow)
- Netflix
- Lyft
- Adobe
- Twitter

And thousands of data teams worldwide! 🌍
