FROM python:3.12-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Set PYTHONPATH so we can import src
ENV PYTHONPATH=/app

# Command to run worker and simulator
CMD ["python", "-m", "src.main"]
