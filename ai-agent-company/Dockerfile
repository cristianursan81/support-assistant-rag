FROM python:3.11-slim

WORKDIR /app

# Install deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data dir for SQLite persistence (mount as volume)
RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite:////app/data/gestor.db

EXPOSE 8000 7861

CMD ["python", "run.py"]
