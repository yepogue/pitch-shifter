# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web_app.py .
COPY pitch_shifter.py .
COPY templates templates/

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Start application using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion
CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120 --access-logfile - --error-logfile - --log-level debug web_app:app"
