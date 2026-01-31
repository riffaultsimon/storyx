FROM python:3.12-slim

# Install ffmpeg (required by pydub for MP3 encoding)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media directories for audio/covers/bgm storage
RUN mkdir -p /app/media/audio /app/media/covers /app/media/bgm

# Streamlit config: disable CORS/XSRF for Cloud Run, set port from env
RUN mkdir -p /app/.streamlit && \
    cat > /app/.streamlit/config.toml <<'TOML'
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFF9E6"
secondaryBackgroundColor = "#FFF3CC"
textColor = "#2D3436"
font = "sans serif"

[server]
port = 8080
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 50

[browser]
gatherUsageStats = false
TOML

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/_stcore/health')"

ENTRYPOINT ["streamlit", "run", "app.py"]
