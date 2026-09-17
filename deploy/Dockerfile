# SAKEC Technology Business Incubator (TBI) Platform
# Production Dockerfile for SAKEC College Server Deployment
# Developed by Dr. Rohan Appasaheb Borgalli

FROM python:3.11-slim

LABEL maintainer="Dr. Rohan Appasaheb Borgalli <incubation@sakec.ac.in>"
LABEL description="SAKEC Technology Business Incubator Management Platform"

ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    SAKEC_DB_PATH=/app/data/sakec_tbi.db

WORKDIR /app

# Copy application source code
COPY database.py simulator.py server.py ./
COPY static/ ./static/

# Create persistent data storage directory
RUN mkdir -p /app/data && chmod 775 /app/data

# Initialize database schema and pre-seeded SAKEC startups
RUN python3 database.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/analytics/portfolio').read()" || exit 1

CMD ["python3", "server.py"]
