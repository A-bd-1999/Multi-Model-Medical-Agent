"""
flask_app.py - Flask Web Server
================================
يشغّل الـ API والـ Frontend على http://localhost:5000
"""

import json
import logging
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.controller import analyse_xray, get_patient_result, list_all_patients
from chatbot.chatbot_engine import ChatbotEngine

# ── Setup ──────────────────────────────────────────────────────
app     = Flask(__name__, static_folder="frontend")
CORS(app)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

chatbot = ChatbotEngine()


# ══════════════════════════════════════════════════════════════
# FRONTEND  —  يفتح index.html تلقائياً
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


# ══════════════════════════════════════════════════════════════
# API — PATIENTS
# ══════════════════════════════════════════════════════════════

@app.route("/api/patients", methods=["GET"])
def api_list_patients():
    limit        = request.args.get("limit", 50, type=int)
    data, status = list_all_patients(limit=limit)
    return jsonify(data), status


@app.route("/api/patients/<int:patient_id>", methods=["GET"])
def api_get_patient(patient_id):
    data, status = get_patient_result(patient_id)
    return jsonify(data), status


# ══════════════════════════════════════════════════════════════
# API — ANALYSE X-RAY
# ══════════════════════════════════════════════════════════════

@app.route("/api/add_patient", methods=["POST"])
def api_add_patient():
    """Add a patient without requiring an X-ray file."""
    body         = request.get_json(silent=True) or {}
    patient_name = str(body.get("patient_name", "")).strip()
    age_raw      = body.get("age", "")
    model_type   = str(body.get("model_type", "")).strip().lower()
    finding      = str(body.get("finding", "Pending analysis")).strip()

    try:
        age = int(age_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Age must be a number."}), 400

    from backend.controller import add_patient
    data, status = add_patient(patient_name, age, model_type, finding)
    return jsonify(data), status


@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    patient_name = request.form.get("patient_name", "").strip()
    age_raw      = request.form.get("age", "")
    model_type   = request.form.get("model_type", "").strip().lower()
    file_obj     = request.files.get("xray_file")

    # -- validate age
    try:
        age = int(age_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Age must be a number."}), 400

    filename = file_obj.filename if file_obj else ""

    data, status = analyse_xray(
        patient_name=patient_name,
        age=age,
        model_type=model_type,
        file_obj=file_obj,
        filename=filename,
    )
    return jsonify(data), status


# ══════════════════════════════════════════════════════════════
# API — CHATBOT
# ══════════════════════════════════════════════════════════════

@app.route("/api/chatbot", methods=["POST"])
def api_chatbot():
    body  = request.get_json(silent=True) or {}
    query = body.get("query", "").strip()

    if not query:
        return jsonify({"status": "error", "message": "query is required."}), 400

    result = chatbot.handle_query(query)
    return jsonify({"status": "ok", "data": result}), 200


# ══════════════════════════════════════════════════════════════
# API — HEALTH CHECK
# ══════════════════════════════════════════════════════════════

@app.route("/api/health", methods=["GET"])
def api_health():
    from database.db_connection import DatabaseConnection
    db   = DatabaseConnection()
    mode = db.mode
    db.close()
    return jsonify({
        "status":   "ok",
        "database": mode,
        "routes":   4,
    }), 200


# ══════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    print("\n" + "=" * 50)
    print("  Medical Agent — Flask Server")
    print("  http://localhost:5000")
    print("  http://localhost:5000/api/health")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)