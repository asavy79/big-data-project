FROM python:3.12-slim

WORKDIR /app

COPY services/matching_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/matching_service ./matching_service

ENV PORT=8080

CMD sh -c "uvicorn matching_service.main:app --host 0.0.0.0 --port ${PORT}"
