
import os
import secrets

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    Depends
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import BaseModel, Field
from typing import Literal

from rag_pipeline import get_answer


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN")

security = HTTPBearer()


# ==========================================
# 2. REQUEST MODELS
# ==========================================

class ChatMessage(BaseModel):

    role: Literal["user", "assistant"]

    content: str = Field(
        min_length=1,
        max_length=4000
    )


class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )

    chat_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20
    )


# ==========================================
# 3. AUTHENTICATION
# ==========================================

def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if not ADMIN_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Admin API token is not configured."
        )

    if not secrets.compare_digest(
        credentials.credentials,
        ADMIN_API_TOKEN
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )

    return "admin"


# ==========================================
# 4. INITIALIZE FASTAPI
# ==========================================

app = FastAPI(
    title="VivPay Role-Based RAG API",
    description="AI Financial Operations and Customer Service Platform",
    version="2.0.0"
)


# ==========================================
# 5. HEALTH CHECK
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
        "status": "ready",
        "supported_formats": ["PDF", "CSV", "XLSX"],
        "storage": "In-memory processing"
    }


# ==========================================
# 6. COMMON CHAT FUNCTION
# ==========================================

def process_question(role, request):

    try:

        history = [
            message.model_dump()
            for message in request.chat_history
        ]

        result = get_answer(
            role=role,
            question=request.question,
            chat_history=history
        )

        return {
            "role": role,
            "question": request.question,
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
# 7. ADMIN CHAT
# ==========================================

@app.post("/admin/chat")
def admin_chat(
    request: ChatRequest,
    role: str = Depends(verify_admin)
):

    return process_question(
        role="admin",
        request=request
    )


# ==========================================
# 8. CUSTOMER CHAT
# ==========================================

@app.post("/customer/chat")
def customer_chat(request: ChatRequest):

    return process_question(
        role="customer",
        request=request
    )


# ==========================================
# 9. API INFORMATION
# ==========================================

@app.get("/api-info")
def api_info():

    return {
        "project": "VivPay",
        "framework": "FastAPI",
        "llm": "Groq",
        "vector_database": "FAISS",
        "embedding_model": "all-MiniLM-L6-v2",
        "features": [
            "Admin RAG",
            "Customer RAG",
            "Conversation History"
        ],
        "endpoints": [
            "/admin/chat",
            "/customer/chat",
            "/health"
        ]
    }
