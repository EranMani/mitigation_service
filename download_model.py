# download_model.py
from sentence_transformers import SentenceTransformer
import os

# Define where we want to save the model inside the container
MODEL_PATH = "/app/models/all-MiniLM-L6-v2"

print(f"Downloading model to {MODEL_PATH}...")
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save(MODEL_PATH)
print("Model saved successfully!")