# Financial Trading ETL Pipeline - Airflow Docker Image
FROM apache/airflow:2.7.3-python3.11

# Switch to root user to install system dependencies
USER root

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        vim \
        less \
        openjdk-17-jdk-headless \
    && mkdir -p /tmp/ta-lib-src \
    && curl -sSL http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz -o /tmp/ta-lib.tar.gz \
    && tar -xzf /tmp/ta-lib.tar.gz -C /tmp/ta-lib-src --strip-components=1 \
    && cd /tmp/ta-lib-src \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && rm -rf /tmp/ta-lib-src /tmp/ta-lib.tar.gz \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Switch back to airflow user
USER airflow

# Copy requirements for Airflow image (excludes airflow itself)
COPY requirements-airflow.txt /requirements-airflow.txt

# Install Python packages
RUN pip install --no-cache-dir -r /requirements-airflow.txt

# Create necessary directories
RUN mkdir -p /opt/airflow/dags \
    && mkdir -p /opt/airflow/logs \
    && mkdir -p /opt/airflow/plugins \
    && mkdir -p /opt/airflow/data

# Set working directory
WORKDIR /opt/airflow

# Note: DAGs, configs, and data will be mounted as volumes from docker-compose