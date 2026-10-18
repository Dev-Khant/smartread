import os
import sys

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
