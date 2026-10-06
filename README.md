# Client Review Request AI Service

A fast, modular **FastAPI** backend service that integrates **MongoDB** and **DeepSeek AI** (`deepseek-chat`) to craft personalized, polite, and effective review request messages for customers who recently used a service but haven't submitted a review yet.

---

## 🌟 Key Features

- **FastAPI Architecture**: High performance, asynchronous API with automatic interactive OpenAPI / Swagger documentation.
- **MongoDB Integration**: Asynchronous database access via `Motor` to retrieve company details (`BusinessProfile`) and client details (`Campaign` / `User`).
- **DeepSeek AI Integration**: Crafts natural, courteous, and non-intrusive messages customized by client name, company name, service type, and communication channel (SMS, WhatsApp, Email).
- **Flexible Options**: Custom tone (friendly, formal, casual), custom language (English, Bengali, etc.), and optional custom business notes.
- **Ready-to-use Endpoints**: Helper endpoints to inspect companies and clients directly from your database.
- **Configured Port**: Runs on **Port 2000**.

---

## 📁 Project Structure

```
mehiditt/
├── app.py                      # FastAPI application entrypoint (runs on port 2000)
├── .env                        # Environment variables (API keys, DB URL, Port)
├── .env.example                # Example environment variables template
├── .gitignore                  # Git ignore rules for Python & sensitive files
├── requirements.txt            # Python package dependencies
├── README.md                   # Complete documentation
│
└── service/                    # Modular service layer
    ├── __init__.py
    ├── database/               # Database management service
    │   ├── __init__.py
    │   └── db_service.py       # Asynchronous Motor client & connection lifecycle
    ├── company/                # Company data service
    │   ├── __init__.py
    │   └── company_service.py  # Retrieves business info from MongoDB
    ├── client/                 # Client/Customer data service
    │   ├── __init__.py
    │   └── client_service.py   # Retrieves client/campaign records from MongoDB
    ├── ai/                     # DeepSeek AI service
    │   ├── __init__.py
    │   └── deepseek_service.py # DeepSeek chat completions API client
    └── review/                 # Review request orchestration
        ├── __init__.py
        └── review_service.py   # Synthesizes data and prompts DeepSeek
```

---

## 🚀 Setup & Installation

### 1. Activate the Virtual Environment

On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
Or (Command Prompt):
```cmd
venv\Scripts\activate.bat
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Ensure your `.env` file contains your credentials (see `.env.example`):

```env
DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
DATABASE_URL="mongodb+srv://<user>:<password>@cluster0.bls3tyg.mongodb.net/mehdit111_DB?appName=Cluster0"
DATABASE_NAME="mehdit111_DB"
PORT=2000
HOST="0.0.0.0"
DEEPSEEK_BASE_URL="https://api.deepseek.com"
DEEPSEEK_MODEL="deepseek-chat"
```

---

## 🏃 Running the Application

### Option 1: Run directly with Python
```powershell
python app.py
```

### Option 2: Run with Uvicorn
```powershell
uvicorn app:app --host 0.0.0.0 --port 2000 --reload
```

Once started, the service will be available at:
- **Base URL**: `http://localhost:2000`
- **Interactive Swagger Docs**: [http://localhost:2000/docs](http://localhost:2000/docs)
- **ReDoc Documentation**: [http://localhost:2000/redoc](http://localhost:2000/redoc)

---

## 📡 API Reference (3 Core Endpoints)

### 1. Health Check
**`GET /health`**

Verifies server status, MongoDB connection, and DeepSeek API key configuration.

---

### 2. Generate Review Request Message (Core Endpoint)
**`POST /api/generate-review-message`**

Fetches company info (`BusinessProfile`) and client info (`Campaign`) from MongoDB using their respective IDs, and uses DeepSeek AI to generate a polite review request message.

#### Request Body:
```json
{
  "company_id": "6ac0774ee0c1a4a1692696ce",
  "client_id": "6ac0866de0c1a4a1692696d8",
  "service_name": "Lunch & Coffee",
  "channel": "SMS",
  "tone": "friendly and polite",
  "language": "English",
  "custom_instructions": "Keep it under 160 characters"
}
```

#### Response Example:
```json
{
  "success": true,
  "generated_message": "Hi Sarah! Thanks for dining with us at Bella's Cafe House. We'd love to hear about your experience. Your feedback helps us improve and support our team. Please leave a quick review here: https://g.page/r/CbellascafeABCDEFG Thank you!",
  "company": {
    "id": "6ac0774ee0c1a4a1692696ce",
    "name": "Bella's Cafe House",
    "category": "Cafe / Restaurant",
    "review_url": "https://g.page/r/CbellascafeABCDEFG"
  },
  "client": {
    "id": "6ac0866de0c1a4a1692696d8",
    "name": "Sarah Mitchell",
    "phone": "+1 (555) 201-8992",
    "email": null,
    "channel": "SMS"
  },
  "metadata": {
    "ai_model": "deepseek-chat",
    "tokens_used": 145,
    "channel": "SMS",
    "tone": "friendly and polite",
    "language": "English"
  }
}
```

---

### 3. Preview Message (Direct Test without Database)
**`POST /api/preview-message`**

Allows instant message testing with custom company and client details without needing MongoDB ObjectIds:

```json
{
  "company_name": "Sunrise Dental Clinic",
  "company_category": "Healthcare",
  "review_url": "https://g.page/r/sunrise-dental",
  "client_name": "David Miller",
  "service_name": "Dental Cleaning",
  "channel": "SMS"
}
```

"# Google_AI_Review" 
