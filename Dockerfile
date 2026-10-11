FROM python:3.11-slim

# Create standard non-root user (UID 1000) for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    SENTIMENT_MODE=auto \
    ALLOW_MODEL_DOWNLOAD=1 \
    DATABASE_URL=/home/user/app/backend/database/riskpulse.db

WORKDIR $HOME/app

# Install Python requirements
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code and data
COPY --chown=user:user . .

# Pre-seed the database so the workspace is immediately ready with live demo data
RUN python scripts/seed_data.py

EXPOSE 7860

# Launch FastAPI app on port 7860 (Hugging Face default)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
