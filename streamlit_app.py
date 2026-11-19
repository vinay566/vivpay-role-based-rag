
import os
import uuid
import requests
import streamlit as st

from statement_processor import process_statement
from statement_rag import get_statement_answer


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="VivPay | AI Financial Assistant",
    page_icon="💳",
    layout="wide"
)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)

MAX_FILE_SIZE = 10 * 1024 * 1024


# ==========================================
# 2. SESSION STATE
# ==========================================

SECTIONS = ["admin", "customer", "statement"]


def create_conversation():

    return {
        "id": str(uuid.uuid4()),
        "title": "New Chat",
        "messages": [],
        "statement_text": None,
        "statement_name": None
    }


for section in SECTIONS:

    history_key = f"{section}_history"
    active_key = f"active_{section}_id"

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    if not st.session_state[history_key]:

        conversation = create_conversation()

        st.session_state[history_key].append(
            conversation
        )

        st.session_state[active_key] = conversation["id"]

    elif active_key not in st.session_state:

        st.session_state[active_key] = (
            st.session_state[history_key][0]["id"]
        )


# ==========================================
# 3. CONVERSATION FUNCTIONS
# ==========================================

def get_active_conversation(section):

    conversations = st.session_state[
        f"{section}_history"
    ]

    active_id = st.session_state[
        f"active_{section}_id"
    ]

    for conversation in conversations:

        if conversation["id"] == active_id:
            return conversation

    conversation = create_conversation()

    conversations.insert(0, conversation)

    st.session_state[
        f"active_{section}_id"
    ] = conversation["id"]

    return conversation


def create_new_chat(section):

    conversation = create_conversation()

    st.session_state[
        f"{section}_history"
    ].insert(0, conversation)

    st.session_state[
        f"active_{section}_id"
    ] = conversation["id"]


def render_history_controls(section):

    conversations = st.session_state[
        f"{section}_history"
    ]

    st.sidebar.subheader("💬 Chat History")

    col1, col2 = st.sidebar.columns(2)

    with col1:

        if st.button(
            "＋ New Chat",
            key=f"new_{section}",
            use_container_width=True
        ):

            create_new_chat(section)
            st.rerun()

    with col2:

        if st.button(
            "🗑 Clear History",
            key=f"clear_{section}",
            use_container_width=True
        ):

            st.session_state[
                f"{section}_history"
            ] = []

            create_new_chat(section)
            st.rerun()

    labels = {
        item["id"]: item["title"]
        for item in conversations
    }

    active_id = st.session_state[
        f"active_{section}_id"
    ]

    if active_id not in labels:
        active_id = conversations[0]["id"]

    selected_id = st.sidebar.selectbox(
        "Previous Conversations",
        options=list(labels.keys()),
        index=list(labels.keys()).index(active_id),
        format_func=lambda item: labels[item],
        key=f"history_select_{section}"
    )

    st.session_state[
        f"active_{section}_id"
    ] = selected_id

    return get_active_conversation(section)


def save_user_message(conversation, question):

    conversation["messages"].append({
        "role": "user",
        "content": question
    })

    if conversation["title"] == "New Chat":
        conversation["title"] = question[:35]


def get_previous_history(conversation):

    # The latest user question is already saved.
    # Exclude it to avoid sending the current question twice.
    return conversation["messages"][:-1]


def display_messages(messages):

    for message in messages:

        with st.chat_message(message["role"]):

            st.write(message["content"])

            if message.get("sources"):

                with st.expander("📄 View Sources"):

                    for source in message["sources"]:
                        st.write(source)


# ==========================================
# 4. CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.main-title {
    font-size: 38px;
    font-weight: bold;
    color: #1769AA;
}

.subtitle {
    color: #718096;
    font-size: 16px;
}

.stButton button {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 5. HEADER
# ==========================================

st.markdown(
    '<div class="main-title">💳 VivPay</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI Financial Operations & Customer Service Platform'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# 6. NAVIGATION
# ==========================================

st.sidebar.title("VivPay Navigation")

role = st.sidebar.radio(
    "Select Portal",
    ["Customer Portal", "Admin Portal"]
)

st.sidebar.divider()


# ==========================================
# 7. CUSTOMER PORTAL
# ==========================================

if role == "Customer Portal":

    customer_section = st.sidebar.radio(
        "Customer Services",
        [
            "Customer FAQ Chat",
            "Bank Statement AI"
        ]
    )

    # --------------------------------------
    # CUSTOMER FAQ CHAT
    # --------------------------------------

    if customer_section == "Customer FAQ Chat":

        conversation = render_history_controls(
            "customer"
        )

        st.header("👤 Customer AI Assistant")

        st.write(
            "Ask questions about payments, "
            "transactions and customer support."
        )

        display_messages(
            conversation["messages"]
        )

        question = st.chat_input(
            "Ask a customer support question...",
            key=f"customer_input_{conversation['id']}"
        )

        if question:

            save_user_message(
                conversation,
                question
            )

            previous_history = get_previous_history(
                conversation
            )

            try:

                with st.spinner(
                    "VivPay AI is thinking..."
                ):

                    response = requests.post(
                        f"{API_BASE_URL}/customer/chat",
                        json={
                            "question": question,
                            "chat_history": previous_history
                        },
                        timeout=90
                    )

                    response.raise_for_status()

                    result = response.json()

                conversation["messages"].append({
                    "role": "assistant",
                    "content": result.get(
                        "answer",
                        "No answer returned."
                    ),
                    "sources": result.get("sources", [])
                })

            except requests.exceptions.RequestException as error:

                conversation["messages"].append({
                    "role": "assistant",
                    "content": f"Customer chatbot error: {error}"
                })

            st.rerun()


    # --------------------------------------
    # BANK STATEMENT AI
    # --------------------------------------

    elif customer_section == "Bank Statement AI":

        conversation = render_history_controls(
            "statement"
        )

        st.header("📄 Bank Statement AI Assistant")

        st.write(
            "Upload a statement and ask questions "
            "about your transactions."
        )

        st.warning(
            "Demonstration only. Use dummy statements. "
            "Customer-specific authentication is not implemented."
        )

        uploaded_file = st.file_uploader(
            "Upload Bank Statement",
            type=["pdf", "csv", "xlsx"],
            key=f"upload_{conversation['id']}"
        )

        if uploaded_file is not None:

            st.write(
                f"Selected file: {uploaded_file.name}"
            )

            if st.button(
                "Process Bank Statement",
                key=f"process_{conversation['id']}"
            ):

                file_bytes = uploaded_file.getvalue()

                if len(file_bytes) > MAX_FILE_SIZE:

                    st.error(
                        "File size must be less than 10 MB."
                    )

                else:

                    try:

                        with st.spinner(
                            "Processing bank statement..."
                        ):

                            extracted_text = process_statement(
                                filename=uploaded_file.name,
                                file_bytes=file_bytes
                            )

                        conversation["statement_text"] = extracted_text
                        conversation["statement_name"] = uploaded_file.name
                        conversation["messages"] = []

                        st.success(
                            "Bank statement processed successfully!"
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Statement processing failed: {error}"
                        )

        # ----------------------------------
        # STATEMENT CONVERSATION
        # ----------------------------------

        if conversation["statement_text"]:

            st.success(
                f"Loaded: {conversation['statement_name']}"
            )

            with st.expander("Preview Statement Data"):

                st.text(
                    conversation["statement_text"][:3000]
                )

            st.divider()

            st.subheader("Ask About Your Transactions")

            display_messages(
                conversation["messages"]
            )

            statement_question = st.chat_input(
                "Ask about your bank transactions...",
                key=f"statement_input_{conversation['id']}"
            )

            if statement_question:

                save_user_message(
                    conversation,
                    statement_question
                )

                previous_history = get_previous_history(
                    conversation
                )

                try:

                    with st.spinner(
                        "Analyzing your bank statement..."
                    ):

                        result = get_statement_answer(
                            question=statement_question,
                            statement_text=conversation["statement_text"],
                            chat_history=previous_history
                        )

                    if isinstance(result, dict):

                        answer = result.get(
                            "answer",
                            "No answer generated."
                        )

                        sources = result.get(
                            "sources",
                            []
                        )

                    else:

                        answer = str(result)
                        sources = []

                    conversation["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

                except Exception as error:

                    conversation["messages"].append({
                        "role": "assistant",
                        "content": f"Statement RAG error: {error}"
                    })

                st.rerun()

        else:

            st.info(
                "Upload and process a statement to start chatting."
            )


# ==========================================
# 8. ADMIN PORTAL
# ==========================================

elif role == "Admin Portal":

    conversation = render_history_controls(
        "admin"
    )

    st.header("🛡️ Admin AI Assistant")

    st.write(
        "Ask questions about fraud policies, "
        "SLA guidelines and internal operations."
    )

    admin_token = st.sidebar.text_input(
        "Admin API Token",
        type="password"
    )

    display_messages(
        conversation["messages"]
    )

    admin_question = st.chat_input(
        "Ask an Admin question...",
        key=f"admin_input_{conversation['id']}"
    )

    if admin_question:

        if not admin_token:

            st.warning(
                "Enter your Admin API token in the sidebar."
            )

        else:

            save_user_message(
                conversation,
                admin_question
            )

            previous_history = get_previous_history(
                conversation
            )

            try:

                with st.spinner(
                    "Admin AI is thinking..."
                ):

                    response = requests.post(
                        f"{API_BASE_URL}/admin/chat",
                        json={
                            "question": admin_question,
                            "chat_history": previous_history
                        },
                        headers={
                            "Authorization": f"Bearer {admin_token}"
                        },
                        timeout=90
                    )

                    response.raise_for_status()

                    result = response.json()

                conversation["messages"].append({
                    "role": "assistant",
                    "content": result.get(
                        "answer",
                        "No answer returned."
                    ),
                    "sources": result.get("sources", [])
                })

            except requests.exceptions.RequestException as error:

                conversation["messages"].append({
                    "role": "assistant",
                    "content": f"Admin chatbot error: {error}"
                })

            st.rerun()


# ==========================================
# 9. FOOTER
# ==========================================

st.divider()

st.caption(
    "© 2026 VivPay | AI Financial Operations "
    "& Customer Service Platform"
)
