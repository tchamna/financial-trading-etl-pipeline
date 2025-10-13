# Financial Trading ETL Pipeline - Airflow Docker Image
FROM apache/airflow:2.8.0-python3.11

# Switch to root user to install system dependencies
USER root

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        vim \
        less \
        openjdk-11-jdk-headless \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Switch back to airflow user
USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r /requirements.txt

# Create necessary directories
RUN mkdir -p /opt/airflow/dags \
    && mkdir -p /opt/airflow/logs \
    && mkdir -p /opt/airflow/plugins \
    && mkdir -p /opt/spark_jobs

# Copy Airflow configuration
COPY airflow.cfg /opt/airflow/airflow.cfg

# Copy DAGs and Spark jobs
COPY airflow_financial_pipeline.py /opt/airflow/dags/
COPY spark/ /opt/spark_jobs/

# Set working directory
WORKDIR /opt/airflow

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=5 \
    CMD curl --fail http://localhost:8080/health || exit 1