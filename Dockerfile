# 1. Use a lightweight Python base image
FROM python:3.12-slim

# 2. Create a folder INSIDE the container named "app"
WORKDIR /app

# 3. Copy files from your Windows "mitigation_service" folder -> to the container's "/app" folder
COPY . .

# 4. Tell Docker we listen on port 8000
EXPOSE 8000

# 5. Run the server when the container starts
CMD ["python", "server.py"]