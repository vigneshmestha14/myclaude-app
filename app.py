import io
import os
import json
import uuid
import base64
from datetime import datetime

import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
from PIL import Image

# ---------- Config ----------
BASE_URL = "https://router.bynara.id/v1"
DEFAULT_MODEL = "mistral-large"

# ⚠️ PASTE YOUR API KEY DIRECTLY HERE OR USE ENV VAR:
MY_API_KEY = os.getenv("OPENAI_API_KEY", "sk-nry-DOPhwx2CiOks_jgf28em2INJmrD8re49KiCae1ikv9s")

HISTORY_FILE = "chat_sessions.json"

st.set_page_config(
    page_title="MyClaude",
    page_icon="✳️",
    layout="wide",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #FAF9F6; }
    section[data-testid="stSidebar"] { background-color: #F0EEE6; }
    .stChatMessage { border-radius: 12px; }
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        text-align: left;
        background-color: transparent;
        border: none;
        color: #3D3929;
        padding: 6px 10px;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #E5E2D9;
    }
    .image-thumb {
        border-radius: 8px;
        margin: 5px 0;
        max-width: 100%;
        max-height: 150px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helper: File Text Extraction ----------
def extract_text_from_file(uploaded_file):
    """Extract text from document uploads."""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_extension in ['txt', 'csv', 'md', 'py', 'json', 'html']:
            return uploaded_file.getvalue().decode("utf-8")
        elif file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        elif file_extension == 'docx':
            doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
    except Exception as e:
        return f"⚠️ Error reading file: {e}"
    return "Unsupported file type."

# ---------- Helper: Encode Image ----------
def encode_image(image_file):
    """Read an image file and return base64 data URL."""
    try:
        image = Image.open(image_file)
        # Convert to RGB if needed (for PNG with alpha)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        # Save to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = "image/jpeg"
        return f"data:{mime_type};base64,{data}"
    except Exception as e:
        st.error(f"Error encoding image: {e}")
        return None

# ---------- Persistent chat sessions ----------
def load_all_sessions():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_sessions(sessions):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

if "sessions" not in st.session_state:
    st.session_state.sessions = load_all_sessions()

if "current_id" not in st.session_state:
    if st.session_state.sessions:
        st.session_state.current_id = max(
            st.session_state.sessions,
            key=lambda k: st.session_state.sessions[k].get("updated_at", ""),
        )
    else:
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {
            "title": "New chat",
            "messages": [],
            "updated_at": datetime.utcnow().isoformat(),
        }
        st.session_state.current_id = new_id
        save_all_sessions(st.session_state.sessions)

# Store uploaded images in session state (for current message)
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []   # list of {"data_url": "...", "name": "..."}

def current_session():
    return st.session_state.sessions[st.session_state.current_id]

def touch_session():
    current_session()["updated_at"] = datetime.utcnow().isoformat()
    save_all_sessions(st.session_state.sessions)

def new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "title": "New chat",
        "messages": [],
        "updated_at": datetime.utcnow().isoformat(),
    }
    st.session_state.current_id = new_id
    st.session_state.uploaded_images = []   # clear images
    save_all_sessions(st.session_state.sessions)

def delete_chat(session_id):
    del st.session_state.sessions[session_id]
    save_all_sessions(st.session_state.sessions)
    if st.session_state.current_id == session_id:
        if st.session_state.sessions:
            st.session_state.current_id = max(
                st.session_state.sessions,
                key=lambda k: st.session_state.sessions[k].get("updated_at", ""),
            )
        else:
            new_chat()

def delete_all_chats():
    st.session_state.sessions.clear()
    save_all_sessions(st.session_state.sessions)
    new_chat()

# ---------- Sidebar ----------
with st.sidebar:
    st.title("✳️ MyClaude")
    st.caption("A Claude-style chat UI with vision support.")

    # --- Chat history at top ---
    st.subheader("💬 Chat History")
    if st.button("＋ New chat", use_container_width=True):
        new_chat()
        st.rerun()

    sorted_ids = sorted(
        st.session_state.sessions.keys(),
        key=lambda sid: st.session_state.sessions[sid].get("updated_at", ""),
        reverse=True,
    )

    if sorted_ids:
        labels = []
        label_to_sid = {}
        for sid in sorted_ids:
            sess = st.session_state.sessions[sid]
            title = sess.get("title") or "New chat"
            updated = sess.get("updated_at", "")
            try:
                dt = datetime.fromisoformat(updated)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = ""
            label = f"{title} ({time_str})" if time_str else title
            labels.append(label)
            label_to_sid[label] = sid

        current_label = None
        for label, sid in label_to_sid.items():
            if sid == st.session_state.current_id:
                current_label = label
                break
        if current_label is None and labels:
            current_label = labels[0]

        selected_label = st.selectbox(
            "Jump to chat",
            options=labels,
            index=labels.index(current_label) if current_label in labels else 0,
            key="chat_select"
        )
        if selected_label and selected_label != current_label:
            target_sid = label_to_sid.get(selected_label)
            if target_sid and target_sid != st.session_state.current_id:
                st.session_state.current_id = target_sid
                st.session_state.uploaded_images = []   # clear images when switching
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Delete all", use_container_width=True):
                if st.checkbox("Confirm delete all?"):
                    delete_all_chats()
                    st.rerun()
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        st.markdown("---")

        for sid in sorted_ids:
            sess = st.session_state.sessions[sid]
            title = sess.get("title") or "New chat"
            is_active = sid == st.session_state.current_id
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(("🟠 " if is_active else "💬 ") + title, key=f"open_{sid}"):
                    if not is_active:
                        st.session_state.current_id = sid
                        st.session_state.uploaded_images = []
                        st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{sid}"):
                    delete_chat(sid)
                    st.rerun()

    st.divider()

    # --- Model settings ---
    model = st.selectbox(
        "Model (vision‑capable recommended)",
        options=[DEFAULT_MODEL, "gpt-4o-mini", "claude-3-5-sonnet"],
        index=0,
    )

    system_prompt = st.text_area(
        "System prompt",
        value="You are a helpful, concise assistant.",
        height=100,
    )

    # --- Document attachment (text files) ---
    st.subheader("📎 Attach a File (text)")
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt", "csv", "md", "py", "json", "html", "pdf", "docx"],
        key="doc_uploader"
    )
    if uploaded_file:
        st.success(f"Attached: {uploaded_file.name}")

    # --- Image attachment (vision) ---
    st.subheader("📷 Attach Image(s)")
    image_files = st.file_uploader(
        "Upload images (JPG, PNG, GIF, WebP)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        accept_multiple_files=True,
        key="image_uploader"
    )
    if image_files:
        for img in image_files:
            # Avoid duplicates: check if already in session state by name (optional)
            data_url = encode_image(img)
            if data_url:
                # Store if not already present (check by name)
                if not any(im.get("name") == img.name for im in st.session_state.uploaded_images):
                    st.session_state.uploaded_images.append({
                        "data_url": data_url,
                        "name": img.name
                    })
        st.rerun()

    # Display uploaded images with remove option
    if st.session_state.uploaded_images:
        st.write(f"**{len(st.session_state.uploaded_images)} image(s) attached**")
        for idx, img_data in enumerate(st.session_state.uploaded_images):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.image(img_data["data_url"], width=120, caption=img_data["name"])
            with col2:
                if st.button("✖", key=f"remove_img_{idx}"):
                    del st.session_state.uploaded_images[idx]
                    st.rerun()
        if st.button("🗑️ Clear all images", use_container_width=True):
            st.session_state.uploaded_images = []
            st.rerun()

    st.divider()

    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.number_input(
        "Max tokens per response",
        min_value=100,
        max_value=8192,
        value=2000,
        step=100
    )

    if st.button("🗑️ Clear current chat", use_container_width=True):
        current_session()["messages"] = []
        st.session_state.uploaded_images = []
        save_all_sessions(st.session_state.sessions)
        st.rerun()

# ---------- Guard: API key ----------
if MY_API_KEY == "your-actual-api-key-here":
    st.error("Please set your API key (or use environment variable OPENAI_API_KEY).")
    st.stop()

client = OpenAI(base_url=BASE_URL, api_key=MY_API_KEY)
sess = current_session()

# ---------- Render chat history ----------
st.title(sess.get("title") if sess.get("title") != "New chat" else "Chat")

for msg in sess["messages"]:
    # For backward compatibility: if content is a string, display as usual
    # If content is a list (vision messages), we need to render images
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], str):
            st.markdown(msg["content"])
        elif isinstance(msg["content"], list):
            # Display each part
            for part in msg["content"]:
                if part["type"] == "text":
                    st.markdown(part["text"])
                elif part["type"] == "image_url":
                    st.image(part["image_url"]["url"], width=200)

# ---------- Chat input ----------
user_input = st.chat_input("Message MyClaude...")

if user_input:
    # Build user message content (text + images)
    content_parts = [{"type": "text", "text": user_input}]
    for img in st.session_state.uploaded_images:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": img["data_url"]}
        })

    # Add to session messages (store as list for vision)
    sess["messages"].append({"role": "user", "content": content_parts})

    # Auto-title
    if sess.get("title") == "New chat":
        sess["title"] = user_input.strip()[:40] + ("…" if len(user_input) > 40 else "")

    touch_session()
    st.session_state.uploaded_images = []   # clear after sending

    # Display user message with images
    with st.chat_message("user"):
        st.markdown(user_input)
        for img in st.session_state.uploaded_images:  # display just after send (they are cleared after, so we need to show before clearing)
            st.image(img["data_url"], width=200)

    # Prepare system prompt + document context
    current_system_prompt = system_prompt
    if uploaded_file:
        file_text = extract_text_from_file(uploaded_file)
        if "⚠️ Error" not in file_text:
            current_system_prompt += (
                f"\n\n--- ATTACHED FILE CONTEXT ---\n"
                f"The user has uploaded a file named '{uploaded_file.name}'. "
                f"Here is the content:\n\n{file_text}\n\n"
                f"Use this context to answer the user's questions."
            )

    # Build API messages: system + history
    # For history, we need to convert stored messages to the format the API expects.
    # Messages stored may have content as string or list. The API expects "content" as string or list.
    # We'll pass them as is.
    api_messages = [{"role": "system", "content": current_system_prompt}] + sess["messages"]

    # Stream assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content or ""
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"⚠️ Request failed: {e}"
            placeholder.markdown(full_response)

    # Store assistant response (plain text)
    sess["messages"].append({"role": "assistant", "content": full_response})
    save_all_sessions(st.session_state.sessions)
    st.rerun()