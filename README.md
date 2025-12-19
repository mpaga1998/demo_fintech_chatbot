# Nova — AI Chatbot Demo 🚀

Nova is a full-stack chatbot demo featuring:

- **React + Vite + Tailwind** frontend
- **FastAPI** backend
- **LangChain + Chroma** for conversational AI with vector search
- Optional **Cloudflare Tunnel** for temporary public demos (no deployment required)

This repository contains a complete end-to-end demo: modern chat UI, multi-session handling, and an AI-powered backend.

---

## 🗂 Project Structure

```
DEMO_CHATBOT/
├─ backend.py
├─ chatbot.py
├─ models.py
├─ requirements.txt
├─ frontend/
│  ├─ src/
│  ├─ vite.config.ts
│  ├─ .env.example
│  └─ package.json
└─ README.md
```

---

## ✨ Features

### Frontend
- Clean chat UI (Nova theme)
- Multiple chat sessions with sidebar
- Mobile-friendly (sidebar collapses into drawer)
- Works locally or via Cloudflare Tunnel

### Backend
- FastAPI server
- `/chat` endpoint
- Conversation memory per session
- Vector store (Chroma) for contextual responses
- CORS enabled for frontend and tunnels

---

## ⚙️ Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- (Optional) `cloudflared` for public demo links

---

## 🧠 Backend Setup

### 1️⃣ Create virtual environment
```bash
python -m venv venv
```

Activate it:

- Windows:
```bash
venv\Scripts\activate
```

- macOS / Linux:
```bash
source venv/bin/activate
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Run backend
```bash
uvicorn backend:app --host 127.0.0.1 --port 8000
```

Verify:
- API docs: http://127.0.0.1:8000/docs
- Endpoint: `POST /chat`

---

## 🖥 Frontend Setup

### 1️⃣ Install dependencies
```bash
cd frontend
npm install
```

### 2️⃣ Environment variables
Create `.env` from the template:

```bash
copy .env.example .env
```

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3️⃣ Run frontend
```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:
```
http://127.0.0.1:5173
```

---

## 🌍 Public Demo (100% Free, Temporary)

This project supports **Cloudflare Quick Tunnels** for demos without deployment.

### 1️⃣ Expose backend
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the generated `https://*.trycloudflare.com` URL.

Update `frontend/.env`:
```env
VITE_API_BASE_URL=https://<BACKEND-TUNNEL-URL>
```

Restart frontend.

### 2️⃣ Expose frontend
```bash
cloudflared tunnel --url http://127.0.0.1:5173
```

Share the **frontend** `trycloudflare.com` link.

---

## 🔐 CORS Configuration

The backend enables CORS for demo purposes:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict `allow_origins`.

---

## 🧪 API Example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "client_type": "cardholder",
    "session_id": "demo"
  }'
```

---

## 🛠 Troubleshooting

### Frontend loads but chat fails
- Ensure backend is running
- Check `VITE_API_BASE_URL`
- Restart Vite after editing `.env`

### `Failed to fetch`
- CORS not enabled
- Tunnel URL changed
- Backend tunnel not running

### Cloudflare host blocked
Ensure `vite.config.ts` includes:
```ts
server: {
  allowedHosts: true
}
```

---

## 📦 Tech Stack

- React
- Vite
- Tailwind CSS
- FastAPI
- LangChain
- ChromaDB
- HuggingFace / Sentence Transformers
- Cloudflare Tunnel (optional)

---

## 📄 License
MIT
