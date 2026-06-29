FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (Python, HTML, CSS, SQL) into the container
COPY . .

EXPOSE 8000

# Run with Uvicorn. Fixed typo: main:app (not main:main)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]