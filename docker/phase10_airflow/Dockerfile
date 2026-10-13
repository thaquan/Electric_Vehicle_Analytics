FROM apache/airflow:slim-2.10.5-python3.11
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir apache-airflow==2.10.5 pyspark==3.5.9 pandas==2.3.3 \
    && pip check
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
