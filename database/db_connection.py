"""
database/db_connection.py - Database Connection (Mock-Safe Version)
====================================================================
Works in TWO modes automatically:
  - REAL mode:  mysql-connector-python installed  -> connects to MySQL
  - MOCK mode:  mysql-connector not installed     -> uses in-memory store
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config import DB_CONFIG

logger = logging.getLogger(__name__)

# -- detect MySQL availability -------------------------------------------------
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    _MYSQL_AVAILABLE = True
except ImportError:
    _MYSQL_AVAILABLE = False
    logger.warning(
        "mysql-connector-python not installed -> running in MOCK mode. "
        "pip install mysql-connector-python  to enable real DB."
    )

# -- in-memory mock store -----------------------------------------------------
_MOCK_STORE: List[Dict] = [
    {"patient_id": 1, "patient_name": "Ahmad Khaled",  "age": 52, "model_type": "bone",
     "model_result": '{"finding":"Hairline fracture in right femur","confidence":0.91}',
     "xray_image": "uploads/xray_001.jpg", "created_at": "2024-03-15 09:12:00"},
    {"patient_id": 2, "patient_name": "Sara Mansour",  "age": 34, "model_type": "lung",
     "model_result": '{"finding":"No significant abnormality","confidence":0.87}',
     "xray_image": "uploads/xray_002.jpg", "created_at": "2024-03-15 10:45:00"},
    {"patient_id": 3, "patient_name": "Omar Farouk",   "age": 67, "model_type": "disease",
     "model_result": '{"finding":"Consolidation pattern suggesting pneumonia","confidence":0.94}',
     "xray_image": "uploads/xray_003.jpg", "created_at": "2024-03-15 14:20:00"},
]
_MOCK_NEXT_ID = 4


class _MockConn:
    def is_connected(self): return True
    def close(self): pass


class DatabaseConnection:
    """MySQL wrapper with automatic in-memory fallback."""

    def __init__(self) -> None:
        self._mock = not _MYSQL_AVAILABLE
        self._conn = None
        if not self._mock:
            self._connect()
        else:
            self._conn = _MockConn()

    def _connect(self) -> None:
        try:
            self._conn = mysql.connector.connect(**DB_CONFIG)
            logger.debug("MySQL connected: host=%s db=%s",
                         DB_CONFIG["host"], DB_CONFIG["database"])
        except Exception as exc:
            logger.error("MySQL failed: %s -> falling back to MOCK.", exc)
            self._mock = True
            self._conn = _MockConn()

    def get_connection(self):
        return self._conn

    def is_connected(self) -> bool:
        return self._conn is not None and self._conn.is_connected()

    def close(self) -> None:
        if not self._mock and self.is_connected():
            self._conn.close()

    # ---------- INSERT -------------------------------------------------------
    def insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        if self._mock:
            return self._mock_insert(params)
        cursor = None
        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            self._conn.commit()
            return cursor.lastrowid
        except Exception as exc:
            logger.error("INSERT failed: %s", exc)
            self._conn.rollback()
            return None
        finally:
            if cursor: cursor.close()

    def _mock_insert(self, params: Tuple) -> int:
        global _MOCK_NEXT_ID
        row = {
            "patient_id":   _MOCK_NEXT_ID,
            "patient_name": params[0] if len(params) > 0 else "Unknown",
            "age":          params[1] if len(params) > 1 else 0,
            "model_type":   params[2] if len(params) > 2 else "unknown",
            "model_result": params[3] if len(params) > 3 else "{}",
            "xray_image":   params[4] if len(params) > 4 else "",
            "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _MOCK_STORE.append(row)
        rid = _MOCK_NEXT_ID
        _MOCK_NEXT_ID += 1
        logger.debug("[MOCK] INSERT patient_id=%d", rid)
        return rid

    # ---------- SELECT -------------------------------------------------------
    def select(self, query: str, params: Tuple = (),
               as_dict: bool = True) -> List[Dict[str, Any]]:
        if self._mock:
            return self._mock_select(query, params)
        cursor = None
        try:
            cursor = self._conn.cursor(dictionary=as_dict)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as exc:
            logger.error("SELECT failed: %s", exc)
            return []
        finally:
            if cursor: cursor.close()

    def _mock_select(self, query: str, params: Tuple) -> List[Dict]:
        q = query.lower()
        rows = list(_MOCK_STORE)

        if "count(*)" in q:
            return [{"total_patients": len(rows)}]

        if "patient_id = %s" in q and params:
            pid = int(params[0])
            rows = [r for r in rows if r["patient_id"] == pid]

        if "model_type = %s" in q and params:
            mt = str(params[0]).lower()
            rows = [r for r in rows if r["model_type"] == mt]

        if "order by created_at desc" in q:
            rows = sorted(rows, key=lambda r: r["created_at"], reverse=True)

        if "limit %s" in q:
            ints = [p for p in params if isinstance(p, int)]
            if ints:
                rows = rows[:ints[-1]]

        logger.debug("[MOCK] SELECT -> %d row(s)", len(rows))
        return rows

    def select_one(self, query: str, params: Tuple = (),
                   as_dict: bool = True) -> Optional[Dict[str, Any]]:
        rows = self.select(query, params, as_dict=as_dict)
        return rows[0] if rows else None

    def __enter__(self): return self
    def __exit__(self, *_): self.close()

    @property
    def mode(self) -> str:
        return "MOCK" if self._mock else "MySQL"