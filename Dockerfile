FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY options_tracker_production.py .
COPY telegram_notifier.py .
COPY data_access.py .
COPY config_loader.py .
COPY config.yaml .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 tracker && chown -R tracker:tracker /app
USER tracker

# Health check endpoint
EXPOSE 8080

CMD ["python", "-u", "options_tracker_production.py"]