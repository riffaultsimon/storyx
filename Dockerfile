# Use the official Python slim image
FROM python:3.12-slim

# Install ffmpeg (required by pydub for MP3 encoding)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
# Layering tip: Copying requirements first speeds up rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media directories for audio/covers/bgm storage
RUN mkdir -p /app/media/audio /app/media/covers /app/media/bgm

# Streamlit config: Create the directory and write config.toml
# We use printf here because it handles newlines and special characters 
# more reliably than 'cat <<TOML' in standard Docker builds.
RUN mkdir -p /app/.streamlit && \
    printf "[theme]\n\
primaryColor = '#FF6B6B'\n\
backgroundColor = '#FFF9E6'\n\
secondaryBackgroundColor = '#FFF3CC'\n\
textColor = '#2D3436'\n\
font = 'sans serif'\n\
\n\
[server]\n\
port = 8080\n\
address = '0.0.0.0'\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
maxUploadSize = 50\n\
\n\
[browser]\n\
gatherUsageStats = false\n" > /app/.streamlit/config.toml

# Cloud Run listens on port 8080 by default
EXPOSE 8080

# Healthcheck to ensure the Streamlit server is responding
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/_stcore/health')"

# Run the application
ENTRYPOINT ["streamlit", "run", "app.py"]