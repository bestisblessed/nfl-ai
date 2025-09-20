# Use ARM64 compatible Python image for Raspberry Pi
FROM python:3.12-slim

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies for ARM64/Raspberry Pi
RUN apt-get update && apt-get install --no-install-recommends -y \
    wget \
    gnupg \
    unzip \
    tzdata \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set timezone to Eastern Time
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
# RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scraper script and shell script
COPY ScraperMasterPFR.py .
COPY scrape_master_pfr.sh .

# Make shell script executable
RUN chmod +x scrape_master_pfr.sh

# Create FINAL directory for output
RUN mkdir -p FINAL

# Run the scraper
CMD ["python", "-u", "ScraperMasterPFR.py"]
