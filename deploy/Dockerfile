FROM python:3.11-slim

LABEL maintainer="Dr. Rohan Appasaheb Borgalli <incubation@sakec.ac.in>"
ENV PYTHONUNBUFFERED=1 PORT=8080 SAKEC_DB_PATH=/app/data/sakec_tbi.db

WORKDIR /app
COPY database.py simulator.py server.py ./
COPY static/ ./static/

RUN mkdir -p /app/data && python3 database.py
EXPOSE 8080
CMD ["python3", "server.py"]
