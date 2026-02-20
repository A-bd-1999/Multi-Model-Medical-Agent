# chatbot/query_builder.py

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ParsedQuery:
    def __init__(self, sql: str, params: Tuple = (), intent: str = "unknown"):
        self.sql    = sql
        self.params = params
        self.intent = intent


_PATTERNS = [
    (r"\b(show|list|get|display|fetch)\s+(all\s+)?patients\b",           "list_all_patients", "_build_list_all"),
    (r"\b(show|get|find|fetch|display)\s+patient\b.*?(\d+)",             "patient_by_id",     "_build_by_id"),
    (r"\b(last|latest|most recent|newest)\s+(result|analysis|record)\b", "last_result",       "_build_last"),
    (r"\b(show|list|get|fetch)\s+(bone|lung|disease)\s+(results?|patients?|records?)\b", "results_by_model", "_build_by_model"),
    (r"\b(how many|count)\s+(all\s+)?patients\b",                        "count_patients",    "_build_count"),
]

DEFAULT_LIMIT = 50


class QueryBuilder:

    def build(self, query: str) -> Optional[ParsedQuery]:
        norm = query.strip().lower()
        for pattern, intent, method in _PATTERNS:
            m = re.search(pattern, norm)
            if m:
                parsed = getattr(self, method)(m, norm)
                parsed.intent = intent
                return parsed
        return None

    def _build_list_all(self, _m, _t) -> ParsedQuery:
        return ParsedQuery(
            sql="SELECT patient_id, patient_name, age, model_type, model_result, created_at FROM patients ORDER BY created_at DESC LIMIT %s",
            params=(DEFAULT_LIMIT,),
        )

    def _build_by_id(self, m, _t) -> ParsedQuery:
        return ParsedQuery(
            sql="SELECT * FROM patients WHERE patient_id = %s LIMIT %s",
            params=(int(m.group(2)), 1),
        )

    def _build_last(self, _m, _t) -> ParsedQuery:
        return ParsedQuery(
            sql="SELECT * FROM patients ORDER BY created_at DESC LIMIT %s",
            params=(1,),
        )

    def _build_by_model(self, _m, text: str) -> ParsedQuery:
        model = next((k for k in ("bone", "lung", "disease") if k in text), "bone")
        return ParsedQuery(
            sql="SELECT patient_id, patient_name, age, model_type, model_result, created_at FROM patients WHERE model_type = %s ORDER BY created_at DESC LIMIT %s",
            params=(model, DEFAULT_LIMIT),
        )

    def _build_count(self, _m, _t) -> ParsedQuery:
        return ParsedQuery(
            sql="SELECT COUNT(*) AS total_patients FROM patients",
            params=(),
        )