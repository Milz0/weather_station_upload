FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir mysql-connector-python==9.2.0
COPY sensor.py mock_services.py test_sensor.py ./
USER 65534:65534
