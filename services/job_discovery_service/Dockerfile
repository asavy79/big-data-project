FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./job_discovery_service/

EXPOSE 8000

CMD ["uvicorn", "job_discovery_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
