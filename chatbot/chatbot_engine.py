# chatbot/chatbot_engine.py

import logging
import re
from typing import Any, Dict, List, Optional

from chatbot.query_builder import QueryBuilder

logger = logging.getLogger(__name__)


class ChatbotEngine:

    def __init__(self) -> None:
        self._qb = QueryBuilder()

    def handle_query(self, raw_query: str) -> Dict[str, Any]:
        if not raw_query or not raw_query.strip():
            return self._reply(False, "unknown", "Please enter a question.")
        raw_query = raw_query.strip()
        
        # ✅ جديد — كشف ID مباشرة
        patient_id = self._extract_id(raw_query)
        if patient_id:
            return self._get_by_id(patient_id)
        
        rtype = self._classify(raw_query)
        if rtype == "ask_patient_info":
            return self._ask_patient(raw_query)
        if rtype == "add_patient_info":
            return self._reply(True, "add_patient_info",
                               "Use the X-ray upload form to add a new patient.")
        return self._reply(True, "general_question", self._knowledge(raw_query))

    # ✅ جديد — استخراج ID من النص
    @staticmethod
    def _extract_id(query: str) -> Optional[int]:
        """
        يكشف إذا المستخدم يسأل عن مريض برقم ID.
        
        أمثلة:
            "patient 5"       → 5
            "show id 12"      → 12
            "get patient #7"  → 7
            "patient id: 3"   → 3
            "#15"             → 15
        """
        q = query.lower()
        
        # نمط 1: patient 5 / patient id 5 / id 5
        m = re.search(r'\b(?:patient\s*(?:id\s*)?|id\s*)[:=\s]*(\d+)\b', q)
        if m:
            return int(m.group(1))
        
        # نمط 2: #5 في بداية أو آخر الجملة
        m = re.search(r'(?:^|\s)#(\d+)(?:\s|$)', q)
        if m:
            return int(m.group(1))
        
        # نمط 3: show/get + رقم لوحده
        if any(word in q for word in ('show', 'get', 'find', 'fetch')):
            m = re.search(r'\b(\d+)\b', q)
            if m:
                return int(m.group(1))
        
        return None

    # ✅ جديد — جلب مريض بالـ ID
    def _get_by_id(self, patient_id: int) -> Dict[str, Any]:
        """جلب معلومات مريض واحد بالـ ID."""
        try:
            from database.db_connection import DatabaseConnection
            with DatabaseConnection() as db:
                row = db.select_one(
                    "SELECT * FROM patients WHERE patient_id = %s",
                    (patient_id,)
                )
        except Exception as exc:
            logger.error("DB error fetching patient %d: %s", patient_id, exc)
            return self._reply(False, "ask_patient_info", 
                             f"Database error while fetching patient #{patient_id}.")
        
        if not row:
            return self._reply(False, "ask_patient_info",
                             f"❌ No patient found with ID #{patient_id}.",
                             data=None)
        
        # تنسيق الرد
        formatted = self._fmt_single_patient(row)
        return self._reply(True, "ask_patient_info", formatted, data=[row])

    @staticmethod
    def _fmt_single_patient(p: Dict) -> str:
        """تنسيق معلومات مريض واحد بشكل واضح."""
        finding = "—"
        confidence = "—"
        try:
            import json
            result = json.loads(p.get("model_result", "{}"))
            finding = result.get("finding", p.get("model_result", "—"))
            conf_val = result.get("confidence")
            if conf_val is not None:
                confidence = f"{float(conf_val)*100:.0f}%"
        except:
            finding = str(p.get("model_result", "—"))[:100]
        
        return f"""📋 **Patient Record**

🆔 ID          : {p.get('patient_id', '?')}
👤 Name        : {p.get('patient_name', '?')}
🎂 Age         : {p.get('age', '?')} years
🔬 Model Type  : {str(p.get('model_type', '?')).upper()}
📊 Finding     : {finding}
✅ Confidence  : {confidence}
🩻 X-Ray Image : {p.get('xray_image') or 'Not available'}
📅 Date        : {p.get('created_at', '?')}"""

    def _ask_patient(self, query: str) -> Dict[str, Any]:
        parsed = self._qb.build(query)
        if not parsed:
            return self._reply(False, "ask_patient_info", 
                             "Could not parse your query. Try: 'show all patients' or 'patient 5'")
        rows = self._run_query(parsed.sql, parsed.params)
        if rows is None:
            return self._reply(False, "ask_patient_info", "Database error.")
        if not rows:
            return self._reply(True, "ask_patient_info", "No records found.", data=[])
        return self._reply(True, "ask_patient_info", self._fmt_rows(rows), data=rows)

    @staticmethod
    def _classify(q: str) -> str:
        q = q.lower()
        if any(k in q for k in ("add patient", "new patient", "insert patient")):
            return "add_patient_info"
        if any(k in q for k in ("patient", "result", "record", "show", "list",
                                 "get", "find", "count", "how many")):
            return "ask_patient_info"
        return "general_question"

    def _run_query(self, sql: str, params: tuple) -> Optional[List]:
        try:
            from database.db_connection import DatabaseConnection
            with DatabaseConnection() as db:
                return db.select(sql, params)
        except Exception as exc:
            logger.error("DB error: %s", exc)
            return None

    @staticmethod
    def _fmt_rows(rows: List[Dict]) -> str:
        """تنسيق قائمة مرضى."""
        lines = [f"Found {len(rows)} record(s):\n"]
        for r in rows:
            if "total_patients" in r:
                lines.append(f"  📊 Total patients: {r['total_patients']}")
                continue
            
            finding = "—"
            try:
                import json
                result = json.loads(r.get("model_result", "{}"))
                finding = result.get("finding", str(r.get("model_result", "")))[:60]
            except:
                finding = str(r.get("model_result", ""))[:60]
            
            lines.append(
                f"  🆔 [{r.get('patient_id','?')}] "
                f"👤 {r.get('patient_name','?')} | "
                f"Age {r.get('age','?')} | "
                f"🔬 {str(r.get('model_type','')).upper()} | "
                f"📝 {finding}"
            )
        return "\n".join(lines)

    _KB = {
        "pneumonia":  "🫁 Pneumonia is a lung infection causing inflammation of air sacs. On X-ray it appears as opacity (white area) in the lung fields.",
        "fracture":   "🦴 A fracture is a break in bone continuity, visible on X-ray as a discontinuous line in the bone structure.",
        "bone":       "🦴 The bone model detects fractures, bone density changes, and structural abnormalities such as osteoporosis or tumours.",
        "lung":       "🫁 The lung model detects pneumonia, pleural effusion, pulmonary oedema, and nodules in chest X-rays.",
        "disease":    "🔬 The disease model performs generalised pathology pattern recognition across multiple organ systems from radiographic imaging.",
        "x-ray":      "🩻 X-rays use electromagnetic radiation to create images of internal structures, especially useful for bones and chest organs.",
        "xray":       "🩻 X-rays use electromagnetic radiation to create images of internal structures, especially useful for bones and chest organs.",
        "osteopenia": "🦴 Osteopenia is reduced bone mineral density, a precursor to osteoporosis, detectable on bone X-rays.",
        "effusion":   "🫁 Pleural effusion is fluid accumulation in the space around the lungs, appearing as haziness at lung bases on X-ray.",
    }

    def _knowledge(self, query: str) -> str:
        q = query.lower()
        for kw, ans in self._KB.items():
            if kw in q:
                return ans
        return (
            "I can help you with:\n"
            "• 'show all patients' — list all records\n"
            "• 'patient 5' or '#5' — get patient by ID\n"
            "• 'count patients' — total count\n"
            "• 'list lung patients' — filter by model\n"
            "• Ask medical questions like 'what is pneumonia?'"
        )

    @staticmethod
    def _reply(success: bool, rtype: str, message: str,
               data: Optional[List] = None) -> Dict[str, Any]:
        return {"success": success, "request_type": rtype,
                "message": message, "data": data}
"""```

---

### التحسينات:

✅ **1. كشف ID تلقائي** — يفهم كل هالأنماط:
- `patient 5`
- `show patient id 12`
- `get #7`
- `patient id: 3`
- `find 15`

✅ **2. رد منسّق أفضل** — لما تسأل عن مريض بالـ ID يعطيك:
```
📋 **Patient Record**

🆔 ID          : 5
👤 Name        : Ahmad Khaled
🎂 Age         : 52 years
🔬 Model Type  : BONE
📊 Finding     : Hairline fracture in right femur
✅ Confidence  : 91%
🩻 X-Ray Image : uploads/xray_005.jpg
📅 Date        : 2024-03-15 09:12"""