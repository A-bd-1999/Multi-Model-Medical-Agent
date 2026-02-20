"""
backend/controller.py - Request Controllers
===========================================
Handles all incoming API requests for X-ray analysis.
Responsibilities:
  - Input validation
  - Orchestrating the model dispatcher
  - Persisting results to the database
  - Returning structured JSON responses
"""

import json
import logging
import os
from typing import Any, Dict, Tuple

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from backend.model_dispatcher import ModelDispatcher
from database.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# MODULE-LEVEL SINGLETONS (created once per process)
# ─────────────────────────────────────────────
_dispatcher = ModelDispatcher()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _allowed_file(filename: str) -> bool:
    """
    Checks that the file has an allowed extension.

    Args:
        filename: Original filename from the upload.

    Returns:
        True if the extension is whitelisted, False otherwise.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def _json_ok(data: Any, status: int = 200) -> Tuple[Dict, int]:
    """Returns a success JSON envelope."""
    return {"status": "ok", "data": data}, status


def _json_error(message: str, status: int = 400) -> Tuple[Dict, int]:
    """Returns an error JSON envelope."""
    logger.warning("Controller error [%d]: %s", status, message)
    return {"status": "error", "message": message}, status


def _save_upload(file_obj: Any, filename: str) -> str:
    """
    Saves an uploaded file to UPLOAD_FOLDER.

    Args:
        file_obj: File-like object with a .save() method (e.g. Flask FileStorage).
        filename: Sanitised target filename.

    Returns:
        Full file-system path where the file was saved.
    """
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(save_path)
    logger.debug("File saved → %s", save_path)
    return save_path


# ─────────────────────────────────────────────
# CONTROLLERS
# ─────────────────────────────────────────────

def analyse_xray(
    patient_name: str,
    age: int,
    model_type: str,
    file_obj: Any,
    filename: str,
) -> Tuple[Dict, int]:
    """
    Handles a complete X-ray analysis request.

    Flow:
      1. Validate all inputs.
      2. Save the uploaded image.
      3. Dispatch to the correct AI model.
      4. Persist the result in the database.
      5. Return structured JSON.

    Args:
        patient_name: Doctor-supplied patient name.
        age:          Patient age (must be 0–120).
        model_type:   One of 'bone', 'lung', 'disease'.
        file_obj:     Upload file object (Flask FileStorage or similar).
        filename:     Original filename of the upload.

    Returns:
        Tuple of (response_dict, http_status_code).
    """
    # ── 1. Validate inputs ──────────────────────────
    if not patient_name or not patient_name.strip():
        return _json_error("patient_name is required.")

    if not isinstance(age, int) or not (0 <= age <= 120):
        return _json_error("age must be an integer between 0 and 120.")

    if not model_type:
        return _json_error("model_type is required.")

    if file_obj is None or filename == "":
        return _json_error("No X-ray file was provided.")

    if not _allowed_file(filename):
        return _json_error(
            f"File type not allowed. Accepted: {ALLOWED_EXTENSIONS}"
        )

    # ── 2. Save uploaded image ──────────────────────
    try:
        image_path = _save_upload(file_obj, filename)
    except OSError as exc:
        return _json_error(f"Could not save uploaded file: {exc}", status=500)

    # ── 3. Model dispatch ───────────────────────────
    try:
        prediction = _dispatcher.dispatch(model_type, image_path)
    except ValueError as exc:
        return _json_error(str(exc), status=400)
    except RuntimeError as exc:
        return _json_error(str(exc), status=500)

    # ── 4. Persist to database ──────────────────────
    model_result_json = json.dumps(prediction["raw"])

    try:
        db = DatabaseConnection()
        patient_id = db.insert(
            """
            INSERT INTO patients
                (patient_name, age, model_type, model_result, xray_image)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                patient_name.strip(),
                age,
                prediction["model_type"],
                model_result_json,
                image_path,
            ),
        )
        db.close()
    except Exception as exc:           # noqa: BLE001
        logger.error("Database insert failed: %s", exc)
        return _json_error("Result could not be saved to database.", status=500)

    # ── 5. Return response ──────────────────────────
    response_payload = {
        "patient_id":   patient_id,
        "patient_name": patient_name.strip(),
        "age":          age,
        "model_type":   prediction["model_type"],
        "finding":      prediction["finding"],
        "confidence":   prediction["confidence"],
        "image_path":   image_path,
    }

    logger.info(
        "Analysis complete — patient_id=%s  model=%s  finding=%s",
        patient_id,
        prediction["model_type"],
        prediction["finding"],
    )

    return _json_ok(response_payload, status=200)


def get_patient_result(patient_id: int) -> Tuple[Dict, int]:
    """
    Fetches a single patient's analysis result by ID.

    Args:
        patient_id: Integer primary key from the patients table.

    Returns:
        Tuple of (response_dict, http_status_code).
    """
    if not isinstance(patient_id, int) or patient_id <= 0:
        return _json_error("patient_id must be a positive integer.")

    try:
        db = DatabaseConnection()
        row = db.select_one(
            "SELECT * FROM patients WHERE patient_id = %s", (patient_id,)
        )
        db.close()
    except Exception as exc:          # noqa: BLE001
        return _json_error(f"Database error: {exc}", status=500)

    if row is None:
        return _json_error(
            f"No patient found with id={patient_id}.", status=404
        )

    return _json_ok(row)


def add_patient(
    patient_name: str,
    age: int,
    model_type: str,
    finding: str = "Pending analysis",
) -> Tuple[Dict, int]:
    """
    Adds a new patient record WITHOUT requiring an X-ray upload.
    Used by the chatbot panel to register a patient quickly.

    Args:
        patient_name: Patient's full name.
        age:          Patient age (0-120).
        model_type:   One of 'bone', 'lung', 'disease'.
        finding:      Optional finding text (defaults to 'Pending analysis').

    Returns:
        Tuple of (response_dict, http_status_code).
    """
    if not patient_name or not patient_name.strip():
        return _json_error("patient_name is required.")

    try:
        age = int(age)
        if not (0 <= age <= 120):
            return _json_error("age must be between 0 and 120.")
    except (TypeError, ValueError):
        return _json_error("age must be a valid integer.")

    if not model_type or model_type.strip().lower() not in ["bone", "lung", "disease"]:
        return _json_error("model_type must be bone, lung, or disease.")

    import json as _json
    model_result_json = _json.dumps({
        "finding": finding,
        "confidence": 0.0,
        "status": "pending"
    })

    try:
        db = DatabaseConnection()
        patient_id = db.insert(
            """INSERT INTO patients
               (patient_name, age, model_type, model_result, xray_image)
               VALUES (%s, %s, %s, %s, %s)""",
            (patient_name.strip(), age, model_type.strip().lower(),
             model_result_json, None),
        )
        db.close()
    except Exception as exc:
        logger.error("add_patient DB insert failed: %s", exc)
        return _json_error("Could not save patient to database.", status=500)

    return _json_ok({
        "patient_id":   patient_id,
        "patient_name": patient_name.strip(),
        "age":          age,
        "model_type":   model_type.strip().lower(),
        "finding":      finding,
    }, status=201)


def list_all_patients(limit: int = 50) -> Tuple[Dict, int]:
    """
    Returns a paginated list of all patients.

    Args:
        limit: Maximum number of rows to return (default 50).

    Returns:
        Tuple of (response_dict, http_status_code).
    """
    try:
        db = DatabaseConnection()
        rows = db.select(
            "SELECT * FROM patients ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        db.close()
    except Exception as exc:          # noqa: BLE001
        return _json_error(f"Database error: {exc}", status=500)

    return _json_ok({"patients": rows, "count": len(rows)})