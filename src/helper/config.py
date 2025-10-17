import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Access environment variables and store them in variables
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

HOST = os.getenv("HOST", "0.0.0.0")  # Changed from "localhost"
PORT = int(os.getenv("PORT", 5001))


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
