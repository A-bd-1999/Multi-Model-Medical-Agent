# Multi-Model-Medical-Agent
Medical Multi Model AI Agent
Team Project
📁 Project Structure Explanation

Medical Multi-Model AI Agent

هذا الملف يشرح وظيفة كل Folder و File داخل المشروع، حتى يكون العمل منظم وكل عضو يعرف مسؤوليته.

✅ Main Files (Root Level)
🔹 app.py

نقطة تشغيل المشروع (Main Entry Point).

المسؤول عن:

تشغيل التطبيق

ربط Backend مع AI Models

استقبال الطلبات من الواجهة أو الـ Chatbot

إرسال النتائج مرة أخرى

لا يحتوي منطق المودلز نفسه، فقط تشغيل وربط النظام.

🔹 config.py

ملف الإعدادات العامة للمشروع.

يحتوي على:

اسم قاعدة البيانات

إعدادات الاتصال

أسماء المودلز

مسارات الملفات

أي إعدادات مشتركة بين الفريق

الهدف منه تجنب كتابة الإعدادات داخل الكود.

🔹 requirements.txt

قائمة المكتبات المستخدمة في المشروع.

أي عضو جديد في الفريق يستطيع تثبيت كل المتطلبات باستخدام:

pip install -r requirements.txt

🔹 README.md

ملف شرح المشروع.

يحتوي على:

فكرة المشروع

آلية عمل النظام

هيكل المشروع

طريقة التشغيل

شرح الملفات

🔹 .gitignore

يحدد الملفات التي لا يجب رفعها على GitHub مثل:

ملفات البيئة الافتراضية

ملفات الكاش

الملفات المؤقتة

الملفات السرية

✅ Project Folders
🔹 backend/

مسؤول عن منطق النظام (System Logic).

يحتوي على:

استقبال طلبات الدكتور

إرسال الصور للمودل المناسب

استقبال النتائج

إرسال النتائج لقاعدة البيانات أو الواجهة

الملفات:

routes.py → تعريف المسارات (API Endpoints)

controller.py → منطق تنفيذ العمليات

model_dispatcher.py → اختيار المودل المناسب حسب نوع الأشعة

utils.py → دوال مساعدة

🔹 models/

يحتوي على نماذج الذكاء الاصطناعي.

كل مودل مسؤول عن مرض معين:

bone_model.py → تحليل كسور العظام

lung_model.py → تحليل أمراض الرئة

disease_model.py → مودل عام أو مستقبلي

كل مودل يستقبل صورة ويرجع نتيجة فقط.

🔹 database/

مسؤول عن التعامل مع قاعدة البيانات.

الملفات:

db_connection.py → الاتصال مع MySQL

schema.sql → إنشاء الجداول

queries.sql → أمثلة على الاستعلامات

يتم تخزين:

بيانات المريض

نتيجة التحليل

نوع المودل المستخدم

وقت التحليل

🔹 chatbot/

مسؤول عن التواصل مع الدكتور.

يحتوي على:

استقبال سؤال الدكتور

تحليل السؤال

تحويله إلى SQL Query

إرجاع النتيجة من قاعدة البيانات

الملفات:

chatbot_engine.py

prompt_handler.py

query_builder.py

🔹 frontend/

واجهة المستخدم الخاصة بالطبيب.

حالياً Placeholder فقط، وسيتم لاحقاً:

رفع صور الأشعة

عرض النتائج

التواصل مع Chatbot

🔹 docs/

ملفات التوثيق والرسومات:

Architecture Diagram

System Flow

أي مخططات للنظام

🔹 tests/

ملفات اختبار النظام لاحقاً للتأكد أن كل جزء يعمل بشكل صحيح.

✅ Important Rule for Team

لا يتم تغيير أسماء الفولدرات أو الملفات بدون الرجوع للـ Team Leader.

كل جزء من النظام يجب أن يلتزم بنفس شكل البيانات (Data Format).
# Medical Multi-Model AI Agent

A production-ready Python backend for AI-powered X-ray analysis using multiple specialised models, a MySQL database, and a doctor-facing chatbot.

---

## System Flow

```
Doctor (UI)
    │
    ├── Upload X-Ray ──► AI Model Analysis (bone / lung / disease)
    │                         │
    │                    Generate Result
    │                         │
    │                    Save to Database ──► Medical Database
    │
    └── Ask Question ──► Chatbot Engine
                              │
                         ┌────┴─────────────────┐
                         │                       │
                    Ask Patient Info        General Question
                         │                       │
                    Query Database          Medical AI Model
                         │                       │
                    Prepare Response        Generate Answer
                              │
                         Display Result
                              │
                          End (Doctor)
```

---

## Project Structure

```
medical-multi-model-agent/
│
├── backend/
│   ├── routes.py           # API route registration
│   ├── controller.py       # Request handling & validation
│   └── model_dispatcher.py # Routes requests to correct AI model
│
├── models/
│   ├── bone_model.py       # Bone X-ray analyser (stub)
│   ├── lung_model.py       # Lung X-ray analyser (stub)
│   └── disease_model.py    # Disease pattern detector (stub)
│
├── database/
│   ├── db_connection.py    # MySQL connection & query helpers
│   ├── schema.sql          # Table definitions + seed data
│   └── queries.sql         # (optional) named query store
│
├── chatbot/
│   ├── chatbot_engine.py   # Main chatbot orchestrator
│   ├── query_builder.py    # NL → SQL converter
│   └── prompt_handler.py   # (future) prompt templating
│
├── frontend/               # Doctor-facing UI (TBD)
├── docs/                   # Architecture diagrams
├── tests/                  # pytest test suite
│
├── app.py                  # Application entry point
├── config.py               # Centralised configuration
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Quick Start

### 1. Clone & install
```bash
git clone <repo-url>
cd medical-multi-model-agent
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

Or set environment variables directly:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=yourpassword
export DB_NAME=medical_agent_db
```

### 3. Set up the database
```bash
mysql -u root -p < database/schema.sql
```

### 4. Run the application
```bash
python app.py
```

---

## Configuration (`config.py`)

| Key | Default | Description |
|-----|---------|-------------|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | `""` | MySQL password |
| `DB_NAME` | `medical_agent_db` | Target database |
| `UPLOAD_FOLDER` | `uploads/` | X-ray upload directory |
| `DEBUG` | `true` | Enable verbose logging |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyse` | Upload X-ray + run AI analysis |
| `GET` | `/api/patients` | List all patient records |
| `GET` | `/api/patients/<id>` | Get single patient result |
| `POST` | `/api/chatbot` | Send query to chatbot engine |

---

## Chatbot Examples

```
"Show all patients"
"Show patient 7"
"Show last result"
"List lung patients"
"Count patients"
"What is pneumonia?"
"What is a fracture?"
```

---

## Integrating Real AI Models

Each model in `models/` exposes a single `predict(image_path)` function.
Replace the stub body with your actual inference code:

```python
# models/bone_model.py
import tensorflow as tf

_MODEL = tf.keras.models.load_model("weights/bone_model.h5")

def predict(image_path: str) -> dict:
    img = preprocess(image_path)
    output = _MODEL.predict(img)
    return {"finding": decode(output), "confidence": float(output.max())}
```

No changes required to dispatcher, controller, or database layers.

---

## Running Tests

```bash
pytest tests/ -v --cov=.
```
