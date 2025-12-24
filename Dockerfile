# 1. Use a standard Python image (Slim is fine, but we need more tools now)
FROM python:3.12-slim

WORKDIR /app

# 2. Install Build Tools (Needed for some AI libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy requirements first (to cache dependencies)
COPY requirements.txt .

# 4. Install dependencies
# --no-cache-dir keeps the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the model downloader script
COPY download_model.py .

# 6. RUN THE DOWNLOADER (This happens during build!)
# This bakes the model into the image so it works offline later.
RUN python download_model.py

# 7. Copy the rest of the app
COPY . .

# 8. Expose ports
EXPOSE 8000
EXPOSE 1344

CMD ["python", "server.py"]