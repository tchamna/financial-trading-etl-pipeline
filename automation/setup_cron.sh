#!/bin/bash

# Daily Financial Data Collection - Cron Setup Script
# Author: Tyler Chamberlain
# Email: tyler.chamberlain@example.com

# This script sets up a daily cron job for automated data collection

PROJECT_PATH="/path/to/your/financial-trading-etl-pipeline"
PYTHON_CMD="python3"
RUN_TIME="0 6 * * *"  # Daily at 6:00 AM

echo "🔧 Setting up Cron Job for Daily Data Collection..."

# Update PROJECT_PATH if provided as argument
if [ "$1" != "" ]; then
    PROJECT_PATH="$1"
fi

echo "Project Path: $PROJECT_PATH"
echo "Python Command: $PYTHON_CMD"
echo "Schedule: Daily at 6:00 AM"

# Create the cron job entry
CRON_JOB="$RUN_TIME cd $PROJECT_PATH && $PYTHON_CMD automation/daily_data_collection.py >> automation/cron.log 2>&1"

echo ""
echo "📋 Cron Job Entry:"
echo "$CRON_JOB"

# Add to crontab
echo ""
echo "Adding to crontab..."
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
else
    echo "❌ Failed to add cron job"
    exit 1
fi

echo ""
echo "📊 Current crontab:"
crontab -l

echo ""
echo "🔧 Manual Commands:"
echo "To view cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
echo "To remove all cron jobs: crontab -r"
echo "To run manually: cd $PROJECT_PATH && $PYTHON_CMD automation/daily_data_collection.py"

echo ""
echo "📝 Log Files:"
echo "Cron execution log: $PROJECT_PATH/automation/cron.log"
echo "Pipeline detailed log: $PROJECT_PATH/automation/daily_collection.log"

echo ""
echo "✅ Setup complete! Daily data collection will run at 6:00 AM."