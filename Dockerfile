# Use official Python runtime
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements (if you have one)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Run scraper when container starts
CMD ["python", "scraper.py"]
