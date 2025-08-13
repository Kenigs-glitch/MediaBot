FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser -m botuser

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for ComfyUI input/output and sessions
RUN mkdir -p /storage/comfyui/input /storage/comfyui/output /app/sessions /app/temp \
    && chown -R botuser:botuser /app /storage

# Switch to non-root user
USER botuser

CMD ["python", "bot.py"] 