import inspect
import os
import requests
import streamlit as st
from dotenv import load_dotenv

from statement_processor import process_statement
from statement_rag import get_statement_answer
from supabase_client import (
    create_conversation,
    save_message,
    get_conversations,
    get_messages,
    delete_conversation,
)

# ==========================================
# 1. CONFIGURATION
# ==========================================

load_dotenv()

st.set_page_config(
    page_title="VivPay AI Platform",
    page_icon="💳",
    layout="wide",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN")

# Demo identity: replace with authenticated user IDs
# before making the application public.
OWNER_IDS = {
    "admin": "admin-demo",
    "customer": "customer-demo",
    "statement": "customer-demo",
}

SECTIONS = {
    "Admin Portal": "admin",
    "Customer FAQ": "customer",
    "Bank Statement AI": "statement",
}

# Streamlit section name -> Supabase database value
DB_TYPES = {
    "admin": "admin",
    "customer": "customer",
    "statement": "bank_statement",
}

# ==========================================
# 2. SESSION STATE
# ==========================================

if "active_section" not in st.session_state:
    st.session_state.active_section = "customer"

if "active_conversations" not in st.session_state:
    st.session_state.active_conversations = {
        "admin": None,
        "customer": None,
        "statement": None,
    }

if "messages_cache" not in st.session_state:
    st.session_state.messages_cache = {}

if "statement_texts" not in st.session_state:
    st.session_state.statement_texts = {}

if "statement_names" not in st.session_state:
    st.session_state.statement_names = {}

# ==========================================
# 3. SUPABASE HELPERS
# ==========================================


def load_section_conversations(section):
    return get_conversations(
        owner_id=OWNER_IDS[section],
        conversation_type=DB_TYPES[section],
    )


def load_conversation(section, conversation_id):
    messages = get_messages(conversation_id)

    st.session_state.messages_cache[conversation_id] = [
        {
            "role": message["message_role"],
            "content": message["content"],
        }
        for message in messages
    ]

    st.session_state.active_conversations[section] = conversation_id


def start_new_chat(section):
    st.session_state.active_conversations[section] = None


def remove_chat(section, conversation_id):
    delete_conversation(conversation_id)

    st.session_state.messages_cache.pop(conversation_id, None)
    st.session_state.statement_texts.pop(conversation_id, None)
    st.session_state.statement_names.pop(conversation_id, None)
    st.session_state.pop(f"sources_{conversation_id}", None)

    if st.session_state.active_conversations[section] == conversation_id:
        st.session_state.active_conversations[section] = None


def get_or_create_conversation(section, question):
    conversation_id = st.session_state.active_conversations[section]

    if conversation_id:
        return conversation_id

    title = question.strip().replace("\n", " ")[:60]

    conversation = create_conversation(
        owner_id=OWNER_IDS[section],
        conversation_type=DB_TYPES[section],
        title=title or "New Chat",
    )

    conversation_id = conversation["id"]

    st.session_state.active_conversations[section] = conversation_id
    st.session_state.messages_cache[conversation_id] = []

    return conversation_id


def add_message(conversation_id, role, content):
    save_message(
        conversation_id=conversation_id,
        message_role=role,
        content=content,
    )

    if conversation_id not in st.session_state.messages_cache:
        st.session_state.messages_cache[conversation_id] = []

    st.session_state.messages_cache[conversation_id].append({
        "role": role,
        "content": content,
    })


def get_chat_history(conversation_id):
    return st.session_state.messages_cache.get(conversation_id, [])


def call_statement_rag(question, statement_text, chat_history):
    sig = inspect.signature(get_statement_answer)
    if "chat_history" in sig.parameters:
        return get_statement_answer(
            question=question,
            statement_text=statement_text,
            chat_history=chat_history,
        )
    return get_statement_answer(
        question=question,
        statement_text=statement_text,
    )


# ==========================================
# 4. SIDEBAR
# ==========================================

st.sidebar.title("💳 VivPay")
st.sidebar.caption("AI Financial Operations Platform")

selected_section = st.sidebar.radio(
    "Choose Portal",
    list(SECTIONS.keys()),
    index=list(SECTIONS.values()).index(st.session_state.active_section),
)

section = SECTIONS[selected_section]
st.session_state.active_section = section

st.sidebar.divider()
st.sidebar.subheader("Chat History")

if st.sidebar.button(
    "➕ New Chat",
    use_container_width=True,
    key=f"new_chat_{section}",
):
    start_new_chat(section)
    st.rerun()

try:
    conversations = load_section_conversations(section)

    if conversations:
        conversation_options = {
            f"{item['title']} · {item['created_at'][:10]}": item["id"]
            for item in conversations
        }

        active_id = st.session_state.active_conversations[section]
        labels = list(conversation_options.keys())

        selected_index = 0
        for index, label in enumerate(labels):
            if conversation_options[label] == active_id:
                selected_index = index
                break

        selected_chat = st.sidebar.selectbox(
            "Previous conversations",
            labels,
            index=selected_index,
            key=f"history_{section}",
        )

        selected_id = conversation_options[selected_chat]

        if selected_id != active_id:
            load_conversation(section, selected_id)
            st.rerun()

        if st.sidebar.button(
            "🗑️ Delete Current Chat",
            use_container_width=True,
            key=f"delete_{section}",
        ):
            remove_chat(section, selected_id)
            st.rerun()
    else:
        st.sidebar.info("No saved conversations yet.")

except Exception as error:
    st.sidebar.error(f"Unable to load history: {error}")
    conversations = []

# ==========================================
# 5. MAIN HEADER
# ==========================================

st.title("💳 VivPay AI Financial Platform")

if section == "admin":
    st.subheader("Admin Portal")
    st.caption("Internal financial policies and operational support.")
elif section == "customer":
    st.subheader("Customer FAQ Assistant")
    st.caption("Ask questions about payments and financial services.")
else:
    st.subheader("Bank Statement AI")
    st.caption("Upload a statement and ask questions about transactions.")

# ==========================================
# 6. DISPLAY CHAT MESSAGES
# ==========================================


def display_messages(conversation_id):
    messages = get_chat_history(conversation_id)

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# ==========================================
# 7. ADMIN AND CUSTOMER CHAT
# ==========================================


def render_api_chat(section):
    conversation_id = st.session_state.active_conversations[section]

    if conversation_id:
        display_messages(conversation_id)

    question = st.chat_input(
        "Ask your question...",
        key=f"chat_input_{section}_{conversation_id or 'new'}",
    )

    if not question:
        return

    try:
        conversation_id = get_or_create_conversation(section, question)
        previous_messages = get_chat_history(conversation_id)

        add_message(conversation_id, "user", question)

        headers = {"Content-Type": "application/json"}

        if section == "admin":
            if not ADMIN_API_TOKEN:
                st.error("ADMIN_API_TOKEN is not configured.")
                return
            headers["Authorization"] = f"Bearer {ADMIN_API_TOKEN}"

        payload = {
            "question": question,
            "chat_history": previous_messages[-10:],
        }

        endpoint = f"{API_BASE_URL}/{section}/chat"

        with st.spinner("VivPay AI is thinking..."):
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()

        answer = result.get("answer", "No answer was returned.")
        add_message(conversation_id, "assistant", answer)
        st.rerun()

    except requests.exceptions.RequestException as error:
        st.error(f"API connection error: {error}")
    except Exception as error:
        st.error(f"Error: {error}")


# ==========================================
# 8. BANK STATEMENT AI
# ==========================================


def render_statement_chat():
    conversation_id = st.session_state.active_conversations["statement"]

    if conversation_id:
        display_messages(conversation_id)

    st.divider()
    st.markdown("### Upload Bank Statement")

    uploaded_file = st.file_uploader(
        "Choose PDF, CSV, or XLSX",
        type=["pdf", "csv", "xlsx"],
        key=f"statement_upload_{conversation_id or 'new'}",
    )

    if uploaded_file:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size must be less than 10 MB.")
            return

        if st.button(
            "Process Statement",
            key=f"process_statement_{conversation_id or 'new'}",
        ):
            try:
                with st.spinner("Processing your statement..."):
                    file_bytes = uploaded_file.getvalue()
                    statement_text = process_statement(
                        filename=uploaded_file.name,
                        file_bytes=file_bytes,
                    )

                if not statement_text:
                    st.warning("No readable text was found.")
                    return

                if not conversation_id:
                    conversation_id = get_or_create_conversation(
                        "statement",
                        f"Statement: {uploaded_file.name}",
                    )

                st.session_state.statement_texts[conversation_id] = statement_text
                st.session_state.statement_names[conversation_id] = uploaded_file.name

                st.success("Statement processed successfully!")
                st.rerun()

            except Exception as error:
                st.error(f"Statement processing failed: {error}")

    conversation_id = st.session_state.active_conversations["statement"]

    if conversation_id:
        statement_text = st.session_state.statement_texts.get(conversation_id)
        statement_name = st.session_state.statement_names.get(conversation_id)

        if statement_text:
            st.success(f"Loaded statement: {statement_name}")

            with st.expander("Preview extracted statement"):
                st.text(statement_text[:5000])
        else:
            st.info(
                "Upload and process the statement again to continue "
                "asking questions in this conversation."
            )

        question = st.chat_input(
            "Ask a question about your statement...",
            key=f"statement_input_{conversation_id}",
        )

        if question:
            if not statement_text:
                st.warning("Please upload and process a statement first.")
                return

            try:
                # 1. Retrieve previous messages BEFORE adding current question
                previous_messages = get_chat_history(conversation_id)

                # 2. Save current user question
                add_message(conversation_id, "user", question)

                # 3. Query Statement RAG
                with st.spinner("Analyzing your statement..."):
                    result = call_statement_rag(
                        question=question,
                        statement_text=statement_text,
                        chat_history=previous_messages[-10:],
                    )

                if isinstance(result, dict):
                    answer = result.get("answer", "No answer was returned.")
                    sources = result.get("sources", [])
                else:
                    answer = str(result)
                    sources = []

                # 4. Save AI response
                add_message(conversation_id, "assistant", answer)

                if sources:
                    st.session_state[f"sources_{conversation_id}"] = sources

                # 5. Refresh chat
                st.rerun()

            except Exception as error:
                st.error(f"Statement AI error: {error}")


# ==========================================
# 9. RENDER SELECTED PORTAL
# ==========================================

if section in ["admin", "customer"]:
    render_api_chat(section)
elif section == "statement":
    render_statement_chat()

# ==========================================
# 10. FOOTER
# ==========================================

st.divider()
st.caption("VivPay | AI Financial Operations & Customer Service Platform")