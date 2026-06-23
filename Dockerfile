# 1. Use a standard production-ready base image
FROM python:3.14-slim

# 2. Set an explicit working directory
WORKDIR /app

# 3. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application assets and code
COPY app.py .
COPY src/ src/
COPY wordList7Letters.txt .

# 5. Set fallback configuration environment variables
ENV CONTENT_TYPE=application/json

# 6. Start Gunicorn, binding to 0.0.0.0 and dynamically utilizing Railway's PORT env var.
# We use shell form here so that the $PORT environment variable evaluates correctly.
CMD gunicorn --bind 0.0.0.0:$PORT app:app