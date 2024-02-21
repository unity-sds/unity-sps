FROM apache/airflow:2.8.1-python3.11

COPY ./airflow/dags/ ${AIRFLOW_HOME}/dags/

RUN pip install cwltool==3.1.20240112164112
