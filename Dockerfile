FROM python:3.12-slim

# Install system dependencies (needed for psycopg2, SQLAlchemy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app (no reload in prod)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
