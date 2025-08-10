
FROM python:3.10-slim

WORKDIR /app

# Copy files with proper structure
COPY etl/ /app/etl/
COPY config/ /app/config/
COPY data/ /app/data/

# Install Python dependencies
RUN pip install --no-cache-dir -r etl/requirements.txt

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run Flask app
CMD ["python", "etl/main.py"]
