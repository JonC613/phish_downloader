FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY streamlit_app.py .
COPY streamlit_app_postgres.py .
COPY phish_ai_client.py .
COPY embedding_generator.py .
COPY phish_json_formatter.py .
COPY phishnet_downloader.py .
COPY __init__.py .

# Create directories
RUN mkdir -p /app/normalized_shows \
    /app/enriched_shows \
    /app/chroma_db \
    /app/data

# Set proper permissions
RUN chmod -R 755 /app

# Create streamlit config
RUN mkdir -p /root/.streamlit
RUN echo '[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
port = 8501\n\
address = "0.0.0.0"\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[theme]\n\
primaryColor = "#1f77b4"\n\
backgroundColor = "#0e1117"\n\
secondaryBackgroundColor = "#262730"\n\
textColor = "#fafafa"\n' > /root/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit (use postgres version if DATABASE_URL is set)
CMD if [ -n "$DATABASE_URL" ]; then \
        streamlit run streamlit_app_postgres.py --server.port=8501 --server.address=0.0.0.0; \
    else \
        streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0; \
    fi
