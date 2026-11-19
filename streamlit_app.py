
import streamlit as st
import requests

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

API_BASE_URL = "http://127.0.0.1:8000"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================
# 2. SESSION STATE
# ==========================================

session_defaults = {
    "admin_messages": [],
    "customer_messages": [],
    "statement_messages": [],
    "statement_text": None,
    "statement_name": None
}

for key, value in session_defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# 3. CUSTOM CSS
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
# 4. HEADER
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
# 5. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("VivPay Navigation")

role = st.sidebar.radio(
    "Select Portal",
    ["Customer Portal", "Admin Portal"]
)

st.sidebar.divider()


# ==========================================
# 6. CUSTOMER PORTAL
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

        st.header("👤 Customer AI Assistant")

        st.write(
            "Ask questions about payments, "
            "transactions and customer support."
        )

        if st.button("Clear FAQ Chat"):

            st.session_state.customer_messages = []
            st.rerun()

        for message in st.session_state.customer_messages:

            with st.chat_message(message["role"]):

                st.write(message["content"])

                if message.get("sources"):

                    with st.expander("View Source Documents"):

                        for source in message["sources"]:
                            st.write(f"📄 {source}")

        question = st.chat_input(
            "Ask a customer support question..."
        )

        if question:

            st.session_state.customer_messages.append({
                "role": "user",
                "content": question
            })

            try:

                with st.spinner("VivPay AI is thinking..."):

                    response = requests.post(
                        f"{API_BASE_URL}/customer/chat",
                        json={"question": question},
                        timeout=90
                    )

                    response.raise_for_status()

                    result = response.json()

                st.session_state.customer_messages.append({
                    "role": "assistant",
                    "content": result.get("answer", "No answer returned."),
                    "sources": result.get("sources", [])
                })

            except requests.exceptions.RequestException as error:

                st.session_state.customer_messages.append({
                    "role": "assistant",
                    "content": f"Customer chatbot error: {error}"
                })

            st.rerun()

    # --------------------------------------
    # CUSTOMER BANK STATEMENT AI
    # --------------------------------------

    elif customer_section == "Bank Statement AI":

        st.header("📄 Bank Statement AI Assistant")

        st.write(
            "Upload a bank statement and ask questions "
            "about your transactions."
        )

        st.warning(
            "Local demonstration only. Use dummy statements. "
            "Customer-specific authentication is not implemented."
        )

        uploaded_file = st.file_uploader(
            "Upload Bank Statement",
            type=["pdf", "csv", "xlsx"],
            key="customer_statement_upload"
        )

        if uploaded_file is not None:

            st.write(
                f"Selected file: {uploaded_file.name}"
            )

            if st.button("Process Bank Statement"):

                file_bytes = uploaded_file.getvalue()

                if len(file_bytes) > MAX_FILE_SIZE:

                    st.error(
                        "File size must be less than 10 MB."
                    )

                else:

                    try:

                        with st.spinner(
                            "Processing your bank statement..."
                        ):

                            extracted_text = process_statement(
                                filename=uploaded_file.name,
                                file_bytes=file_bytes
                            )

                        st.session_state.statement_text = extracted_text
                        st.session_state.statement_name = uploaded_file.name
                        st.session_state.statement_messages = []

                        st.success(
                            "Bank statement processed successfully!"
                        )

                    except Exception as error:

                        st.error(
                            f"Statement processing failed: {error}"
                        )

        # ----------------------------------
        # STATEMENT STATUS
        # ----------------------------------

        if st.session_state.statement_text:

            st.success(
                f"Loaded: {st.session_state.statement_name}"
            )

            with st.expander("Preview Statement Data"):

                st.text(
                    st.session_state.statement_text[:3000]
                )

            st.divider()

            st.subheader("Ask About Your Transactions")

            # Display previous messages

            for message in st.session_state.statement_messages:

                with st.chat_message(message["role"]):

                    st.write(message["content"])

                    if message.get("sources"):

                        with st.expander("View Sources"):

                            for source in message["sources"]:
                                st.write(source)

            # Statement question input

            statement_question = st.chat_input(
                "Ask about your bank transactions...",
                key="statement_chat_input"
            )

            if statement_question:

                st.session_state.statement_messages.append({
                    "role": "user",
                    "content": statement_question
                })

                try:

                    with st.spinner(
                        "Analyzing your bank statement..."
                    ):

                        result = get_statement_answer(
                            question=statement_question,
                            statement_text=st.session_state.statement_text
                        )

                    if isinstance(result, dict):

                        answer = result.get(
                            "answer",
                            "No answer generated."
                        )

                        sources = result.get("sources", [])

                    else:

                        answer = str(result)
                        sources = []

                    st.session_state.statement_messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

                except Exception as error:

                    st.session_state.statement_messages.append({
                        "role": "assistant",
                        "content": f"Statement RAG error: {error}"
                    })

                st.rerun()

            st.divider()

            if st.button("Remove Statement and Clear Chat"):

                st.session_state.statement_text = None
                st.session_state.statement_name = None
                st.session_state.statement_messages = []

                st.rerun()


# ==========================================
# 7. ADMIN PORTAL
# ==========================================

elif role == "Admin Portal":

    st.header("🛡️ Admin AI Assistant")

    st.write(
        "Ask questions about fraud policies, "
        "SLA guidelines and internal operations."
    )

    admin_token = st.sidebar.text_input(
        "Admin API Token",
        type="password"
    )

    if st.button("Clear Admin Chat"):

        st.session_state.admin_messages = []
        st.rerun()

    # Display Admin conversation

    for message in st.session_state.admin_messages:

        with st.chat_message(message["role"]):

            st.write(message["content"])

            if message.get("sources"):

                with st.expander("View Source Documents"):

                    for source in message["sources"]:
                        st.write(f"📄 {source}")

    admin_question = st.chat_input(
        "Ask an Admin question..."
    )

    if admin_question:

        if not admin_token:

            st.warning(
                "Enter your Admin API token in the sidebar."
            )

        else:

            st.session_state.admin_messages.append({
                "role": "user",
                "content": admin_question
            })

            try:

                with st.spinner("Admin AI is thinking..."):

                    response = requests.post(
                        f"{API_BASE_URL}/admin/chat",
                        json={"question": admin_question},
                        headers={
                            "Authorization": f"Bearer {admin_token}"
                        },
                        timeout=90
                    )

                    response.raise_for_status()

                    result = response.json()

                st.session_state.admin_messages.append({
                    "role": "assistant",
                    "content": result.get("answer", "No answer returned."),
                    "sources": result.get("sources", [])
                })

            except requests.exceptions.RequestException as error:

                st.session_state.admin_messages.append({
                    "role": "assistant",
                    "content": f"Admin chatbot error: {error}"
                })

            st.rerun()


# ==========================================
# 8. FOOTER
# ==========================================

st.divider()

st.caption(
    "© 2026 VivPay | AI Financial Operations "
    "& Customer Service Platform"
)
