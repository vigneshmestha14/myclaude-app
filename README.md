# ✳️ MyClaude – A Claude‑style Chat UI

**MyClaude** is a Streamlit‑based chat application that connects to any OpenAI‑compatible API router (e.g., Bynara). It features persistent chat sessions, file attachments (text, PDF, DOCX), **vision support** (images), and a clean Claude‑inspired interface. Deploy it easily to Azure Web App and start chatting with state‑of‑the‑art models.

---

## ✨ Features

- **Multiple chat sessions** – create, switch, rename, and delete conversations.
- **File attachments** – upload `.txt`, `.csv`, `.md`, `.py`, `.json`, `.html`, `.pdf`, `.docx` – the app extracts text and adds it to the context.
- **Vision support** – attach images (JPG, PNG, GIF, WebP) and ask questions about them (requires a vision‑capable model like `gpt-4o` or `claude-3-5-sonnet`).
- **Model selection** – choose from `mistral-large`, `gpt-4o-mini`, `claude-3-5-sonnet`, or any model your router provides.
- **Custom system prompt** – tailor the assistant’s behaviour.
- **Token‑limit removed** – all counting logic stripped out for simplicity and performance.
- **Persistent storage** – chat history is saved to `chat_sessions.json` (local file – ephemeral on Azure unless configured for persistent storage).
- **Deployment ready** – includes `requirements.txt` and startup command for Azure Web App (Linux).

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.10 or 3.11
- An API key from your router (e.g., Bynara)

### 1. Clone or download the project
```bash
git clone https://github.com/your-username/myclaude.git
cd myclaude
```

### 2. Set environment variables

Create a `.env` file or export these values in your shell:

```bash
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://router.bynara.id/v1
OPENAI_MODEL=mistral-large
```

### 3. Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Azure Web App Deployment

This project is ready for Azure App Service on Linux.

Use these app settings in Azure Web App:

- `OPENAI_API_KEY` for your router key
- `OPENAI_BASE_URL` if your router endpoint is different
- `OPENAI_MODEL` if you want a different default model

Set the startup command to:

```bash
bash startup.sh
```

The app listens on `0.0.0.0` and uses the port provided by App Service, or `8000` locally.