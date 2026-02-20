-- Database tables structure
-- =============================================================
-- schema.sql — Medical Multi-Model AI Agent Database Schema
-- =============================================================
-- Engine  : MySQL 8.0+
-- Charset : utf8mb4 (full Unicode, including emoji / special chars)
-- =============================================================

-- Create and select the database
CREATE DATABASE IF NOT EXISTS medical_agent_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE medical_agent_db;

-- =============================================================
-- TABLE: patients
-- Stores each analysed X-ray record along with the AI result.
-- =============================================================
CREATE TABLE IF NOT EXISTS patients (
    patient_id   INT           NOT NULL AUTO_INCREMENT,
    patient_name VARCHAR(150)  NOT NULL,
    age          TINYINT       UNSIGNED NOT NULL,
    model_type   ENUM('bone', 'lung', 'disease') NOT NULL,
    model_result TEXT          NOT NULL,          -- JSON or plain-text AI output
    xray_image   VARCHAR(512)  DEFAULT NULL,      -- File path or base64 reference
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (patient_id),
    INDEX idx_model_type  (model_type),
    INDEX idx_created_at  (created_at)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Stores X-ray analysis results produced by AI models';

-- =============================================================
-- TABLE: analysis_logs
-- Lightweight audit trail of every analysis request.
-- =============================================================
CREATE TABLE IF NOT EXISTS analysis_logs (
    log_id       INT           NOT NULL AUTO_INCREMENT,
    patient_id   INT           DEFAULT NULL,      -- FK to patients (nullable)
    model_type   VARCHAR(50)   NOT NULL,
    status       ENUM('success', 'error') NOT NULL DEFAULT 'success',
    error_msg    TEXT          DEFAULT NULL,
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (log_id),
    CONSTRAINT fk_log_patient
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Audit log for every analysis request';

-- =============================================================
-- SAMPLE SEED DATA (development / testing only)
-- =============================================================
INSERT INTO patients (patient_name, age, model_type, model_result, xray_image)
VALUES
    ('Ahmad Khaled',  52, 'bone',    '{"finding": "hairline fracture detected in right femur", "confidence": 0.91}', 'uploads/xray_001.jpg'),
    ('Sara Mansour',  34, 'lung',    '{"finding": "no significant abnormality detected",          "confidence": 0.87}', 'uploads/xray_002.jpg'),
    ('Omar Farouk',   67, 'disease', '{"finding": "consolidation pattern suggesting pneumonia",   "confidence": 0.94}', 'uploads/xray_003.jpg');
