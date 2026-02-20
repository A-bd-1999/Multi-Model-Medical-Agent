# models/lung_model.py
import logging, os
logger = logging.getLogger(__name__)

def predict(image_path: str) -> dict:
    if image_path and not os.path.isfile(image_path):
        logger.warning("[lung_model] File not found: %s — stub result.", image_path)
    return {"finding": "Lungs appear clear. No significant opacity (stub).",
            "confidence": 0.88, "model": "lung_model_v1.0"}