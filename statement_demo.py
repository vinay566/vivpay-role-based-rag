
import streamlit as st

from statement_processor import process_statement
from statement_rag import get_statement_answer


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="VivPay | Bank Statement AI",
    page_icon="💳",
    layout="wide"
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==========================================
# 2. SESSION STATE
# ==========================================

if "statement_text" not in st.session_state:
    st.session_state.statement_text = None

if "statement_name" not in st.session_state:
    st.session_state.statement_name = None

if "statement_messages" not in st.session_state:
    st.session_state.statement_messages = []


# ==========================================
# 3. CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>
.main-title {
    color: #1769AA;
    font-size: 38px;
    font-weight: bold;
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
    'AI-Powered Bank Statement Analysis'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

st.header("📄 Bank Statement AI Assistant")

st.info(
    "Local demonstration only. Upload a dummy statement, "
    "then ask questions about its transactions."
)


# ==========================================
# 5. UPLOAD BANK STATEMENT
# ==========================================

st.subheader("Upload Your Bank Statement")

uploaded_file = st.file_uploader(
    "Choose a bank statement",
    type=["pdf", "csv", "xlsx"]
)

if uploaded_file is not None:

    st.write("Selected file:", uploaded_file.name)

    if st.button("Process Bank Statement"):

        file_bytes = uploaded_file.getvalue()

        if len(file_bytes) > MAX_FILE_SIZE:

            st.error("File size must be less than 10 MB.")

        else:

            try:

                with st.spinner("Processing bank statement..."):

                    extracted_text = process_statement(
                        filename=uploaded_file.name,
                        file_bytes=file_bytes
                    )

                # Keep extracted text in this Streamlit session only.
                st.session_state.statement_text = extracted_text
                st.session_state.statement_name = uploaded_file.name
                st.session_state.statement_messages = []

                st.success("Bank statement processed successfully!")

            except Exception as error:

                st.error(f"Statement processing failed: {error}")


# ==========================================
# 6. DISPLAY UPLOADED STATEMENT STATUS
# ==========================================

if st.session_state.statement_text:

    st.success(
        f"Loaded statement: {st.session_state.statement_name}"
    )

    with st.expander("Preview extracted statement text"):

        st.text(
            st.session_state.statement_text[:3000]
        )

    st.divider()

    st.subheader("Ask Questions About Your Transactions")

    # ======================================
    # 7. DISPLAY CHAT HISTORY
    # ======================================

    for message in st.session_state.statement_messages:

        with st.chat_message(message["role"]):

            st.write(message["content"])

            if message.get("sources"):

                with st.expander("View Sources"):

                    for source in message["sources"]:
                        st.write(source)

    # ======================================
    # 8. CHAT INPUT
    # ======================================

    question = st.chat_input(
        "Ask about your bank transactions..."
    )

    if question:

        st.session_state.statement_messages.append({
            "role": "user",
            "content": question
        })

        try:

            with st.spinner("Analyzing your statement..."):

                result = get_statement_answer(
                    question=question,
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
                "content": f"Unable to answer your question: {error}"
            })

        st.rerun()


# ==========================================
# 9. CLEAR STATEMENT
# ==========================================

if st.session_state.statement_text:

    st.divider()

    if st.button("Remove Statement and Clear Chat"):

        st.session_state.statement_text = None
        st.session_state.statement_name = None
        st.session_state.statement_messages = []

        st.rerun()


# ==========================================
# 10. FOOTER
# ==========================================

st.divider()

st.caption(
    "VivPay | Bank Statement RAG Demo | Local Testing Only"
)
