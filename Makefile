# Makefile for Mitigation Service

.PHONY: run clean build demo

# COMMAND REQUIRED BY ASSIGNMENT
# We use 'docker compose up' because it is smart:
# 1. If the image exists, it runs it immediately (OFFLINE-FRIENDLY).
# 2. If the image is missing, it tries to build it.
run:
	@echo "Starting the service..."
	docker compose up

# Explicit build command (Only run this when you have internet)
build:
	@echo "Building Docker image (requires internet)..."
	docker compose build

# Stop and Clean
clean:
	@echo "Cleaning up containers..."
	docker compose down

# Run the Automated Demo (Linux)
demo:
	@echo "Running automated demo script..."
	bash run_demo.sh