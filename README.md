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
HOST="127.0.1.0"
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
uvicorn app:app --host 127.0.1.0 --port 2000 --reload
```

### Option 3: Run with Docker Compose (Multi-stage build)
```powershell
docker compose up -d --build
```
To check container status and logs:
```powershell
docker compose ps
docker compose logs -f
```
To stop the container:
```powershell
docker compose down
```

Once started, the service will be available at:
- **Base URL**: `http://127.0.1.0:2000`
- **Interactive Swagger Docs**: [http://127.0.1.0:2000/docs](http://127.0.1.0:2000/docs)
- **ReDoc Documentation**: [http://127.0.1.0:2000/redoc](http://127.0.1.0:2000/redoc)


---

## 📡 API Reference

### 1. Health Check
**`GET /health`**
Verifies server status, MongoDB connection, and DeepSeek API key configuration.

---

### 2. Generate Review Request Message
**`POST /api/generate-review-message`**
Fetches company info (`BusinessProfile`) and client info (`Campaign`) from MongoDB using their respective IDs, and uses DeepSeek AI to generate a polite review request message.

#### Request Body:
```json
{
  "company_id": "6ac0774ee0c1a4a1692696ce",
  "client_id": "6ac0866de0c1a4a1692696d8"
}
```

---

### 3. Competitor Intelligence & Automated Discovery
**`POST /api/competitors/intelligence`**
Analyzes competitor review volumes, growth rates, market positioning, and uses DeepSeek AI to identify competitors within radius (5-10 miles).

#### Request Body:
```json
{
  "business_id": "6ac0774ee0c1a4a1692696ce",
  "radius_miles": 5,
  "limit": 5,
  "auto_identify": false
}
```

---

### 4. Review Gap Analysis
**`POST /api/review-gap/analyze`**
Compares your business review metrics with competitors (gap %, growth difference, timeline chart) and generates actionable DeepSeek AI strategic recommendations.

#### Request Body:
```json
{
  "business_id": "6ac0774ee0c1a4a1692696ce"
}
```

---

### 5. Monthly AI Growth Report
**`POST /api/reports/monthly-growth`**
Generates an attractive, motivational email summary report featuring:
- New reviews gained this month
- Total NFC card taps
- Market rank position vs competitors
- DeepSeek AI visual summary with emojis (🟢, 👍, 🚀, 🏆)

#### Request Body:
```json
{
  "business_id": "6ac0774ee0c1a4a1692696ce",
  "month": "October",
  "year": 2026
}
```

---

### 6. Preview Message (Direct Test without Database)
**`POST /api/preview-message`**
Allows instant review message testing with custom details without requiring MongoDB ObjectIds.
 
