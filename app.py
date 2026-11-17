
import os
import secrets

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pydantic import BaseModel, Field

from rag_pipeline import get_answer



# ==========================================
# 1. AUTHENTICATION CONFIGURATION
# ==========================================

load_dotenv()

ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN")
CUSTOMER_API_TOKEN = os.getenv("CUSTOMER_API_TOKEN")

security = HTTPBearer()


# ==========================================
# 2. AUTHENTICATION FUNCTIONS
# ==========================================

def authenticate_user(credentials, expected_token, role):

    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail=f"{role} token is not configured."
        )

    if not secrets.compare_digest(
        credentials.credentials,
        expected_token
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )

    return role


def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    return authenticate_user(
        credentials,
        ADMIN_API_TOKEN,
        "Admin"
    )


def verify_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    return authenticate_user(
        credentials,
        CUSTOMER_API_TOKEN,
        "Customer"
    )


# ==========================================
# ROLE-BASED AUTHENTICATION
# ==========================================

def authenticate_user(
    credentials: HTTPAuthorizationCredentials,
    expected_token: str,
    role: str
):

    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail=f"{role} API token is not configured."
        )

    if not secrets.compare_digest(
        credentials.credentials,
        expected_token
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )

    return role


def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    return authenticate_user(
        credentials,
        ADMIN_API_TOKEN,
        "Admin"
    )


def verify_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    return authenticate_user(
        credentials,
        CUSTOMER_API_TOKEN,
        "Customer"
    )



# ==========================================
# 1. INITIALIZE FASTAPI
# ==========================================

app = FastAPI(
    title="VivPay Role-Based RAG API",
    description="AI Financial Operations and Customer Service Platform",
    version="1.0.0"
)


# ==========================================
# 2. REQUEST MODEL
# ==========================================

class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )


# ==========================================
# 3. HEALTH CHECK
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Welcome to VivPay Role-Based RAG API",
        "status": "running"
    }


@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "application": "VivPay RAG"
    }


@app.get("/customer/statement/status")
def statement_status():

    return {
        "feature": "Bank Statement RAG",
        "status": "preparing",
        "supported_formats": [
            "PDF",
            "CSV",
            "XLSX"
        ],
        "storage": "In-memory processing",
        "authentication": "Required before upload is enabled"
    }


# ==========================================
# 4. COMMON CHAT FUNCTION
# ==========================================

def process_question(role, question):

    try:

        result = get_answer(
            role=role,
            question=question
        )

        return {
            "role": role,
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print("RAG Error:", str(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer."
        )



# ==========================================
# ADMIN CHAT ENDPOINT
# ==========================================

@app.post("/admin/chat")
def admin_chat(
    request: ChatRequest,
    role: str = Depends(verify_admin)
):

    return process_question(
        role="admin",
        question=request.question
    )




# ==========================================
# CUSTOMER CHAT ENDPOINT
# ==========================================

@app.post("/customer/chat")
def customer_chat(request: ChatRequest):

    return process_question(
        role="customer",
        question=request.question
    )


# ==========================================
# 7. RUN INFORMATION
# ==========================================

@app.get("/api-info")
def api_info():

    return {
        "project": "VivPay",
        "framework": "FastAPI",
        "llm": "Groq",
        "vector_database": "FAISS",
        "embedding_model": "all-MiniLM-L6-v2",
        "endpoints": [
            "/admin/chat",
            "/customer/chat"
        ]
    }
