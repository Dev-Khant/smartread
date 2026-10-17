import os
import sys

# Dummy config so module-level clients can be constructed without real credentials
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MISTRAL_API_KEY", "test")
os.environ.setdefault("GROQ_API_KEY", "test")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
