# Makefile for Mitigation Service

.PHONY: run clean build

# Default target
run:
	@echo "Building and starting the service..."
	docker compose up --build

# Stop and remove containers
clean:
	@echo "Cleaning up containers..."
	docker compose down

# Just build the image
build:
	docker compose build