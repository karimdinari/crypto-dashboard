# Extends the official image so DAG BashOperator tasks can import `app.*`
# with the same dependencies as local `pip install -r requirements.txt`.
FROM apache/airflow:2.9.3

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
