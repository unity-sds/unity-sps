FROM apache/airflow:2.10.3-python3.11

RUN pip install cwltool==3.1.20240112164112
RUN pip install boto3==1.34.89

# code common to all DAGs
COPY airflow/plugins /opt/airflow/plugins
