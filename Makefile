# Makefile for Mitigation Service

.PHONY: run clean build demo

# Build and Start
run:
	@echo "Building and starting the service..."
	docker compose up --build

# Stop and Clean
clean:
	@echo "Cleaning up containers..."
	docker compose down

# Run the Automated Demo (Linux)
demo:
	@echo "Running automated demo script..."
	bash run_demo.sh
