"""
config.py - Central Configuration for Medical Multi-Model AI Agent
==================================================================
Manages all project-level settings including database credentials,
model types, and environment flags.
"""

import os

# ─────────────────────────────────────────────
# PROJECT 
# ─────────────────────────────────────────────
PROJECT_NAME = "Medical Multi-Model AI Agent"
PROJECT_VERSION = "1.0.0"

# ─────────────────────────────────────────────
# DATABASE CONFIGURATION
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "medical_agent_db"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}

# ─────────────────────────────────────────────
# SUPPORTED AI MODEL TYPES
# ─────────────────────────────────────────────
SUPPORTED_MODEL_TYPES = [
    "bone",
    "lung",
    "disease",
]

# ─────────────────────────────────────────────
# MODEL CONFIGURATION
# ─────────────────────────────────────────────
MODEL_CONFIG = {
    "bone": {
        "name":        "Bone X-Ray Analyzer",
        "description": "Detects fractures, density issues, and bone abnormalities.",
        "version":     "1.0",
    },
    "lung": {
        "name":        "Lung X-Ray Analyzer",
        "description": "Detects pneumonia, nodules, and pulmonary conditions.",
        "version":     "1.0",
    },
    "disease": {
        "name":        "Disease Pattern Detector",
        "description": "General disease pattern recognition from X-ray images.",
        "version":     "1.0",
    },
}

# ─────────────────────────────────────────────
# FILE UPLOAD CONFIGURATION
# ─────────────────────────────────────────────
UPLOAD_FOLDER      = os.getenv("UPLOAD_FOLDER", "uploads/")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "dcm"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# ─────────────────────────────────────────────
# CHATBOT CONFIGURATION
# ─────────────────────────────────────────────
CHATBOT_CONFIG = {
    "max_response_rows": 50,
    "default_limit":     10,
}

# ─────────────────────────────────────────────
# DEBUG / ENVIRONMENT
# ─────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ENV   = os.getenv("ENV", "development")  # development | production
