# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install dependencies and sops
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    netcat-openbsd \
    yq \
    && rm -rf /var/lib/apt/lists/*

# Install sops
ENV SOPS_VERSION=v3.10.2
RUN curl -L -o /usr/local/bin/sops \
    https://github.com/getsops/sops/releases/download/${SOPS_VERSION}/sops-${SOPS_VERSION}.linux.amd64 \
    && chmod +x /usr/local/bin/sops

## Install Python dependencies
#COPY requirements.txt /app/
#RUN pip install --no-cache-dir -r requirements.txt

# Copy requirements (without local lib line)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default CMD (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
