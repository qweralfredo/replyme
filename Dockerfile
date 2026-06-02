FROM python:3.12-alpine

WORKDIR /app

# Expose port 8000
EXPOSE 8000

# Command to run (placeholder for now)
CMD ["python", "-m", "http.server", "8000"]
