FROM python:3.12-slim

WORKDIR /app

COPY services/user_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/user_service ./user_service

ENV PORT=8080

CMD sh -c "uvicorn user_service.main:app --host 0.0.0.0 --port ${PORT}"
