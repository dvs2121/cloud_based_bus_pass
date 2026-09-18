FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all files (Python, HTML, CSS, SQL) into the container
COPY . .

EXPOSE 8000

# Run with Uvicorn. Fixed typo: main:app (not main:main)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]