
import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Streamlit Cloud secrets fallback
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing.")

# Server-side client only. Never expose this key in browser code.
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def get_supabase_client():
    return supabase


# Create a new conversation
def create_conversation(owner_id, conversation_type, title="New Chat"):
    result = supabase.table("conversations").insert({
        "owner_id": owner_id,
        "conversation_type": conversation_type,
        "title": title
    }).execute()

    return result.data[0]


# Save a user or assistant message
def save_message(conversation_id, message_role, content):
    result = supabase.table("chat_messages").insert({
        "conversation_id": conversation_id,
        "message_role": message_role,
        "content": content
    }).execute()

    return result.data[0]


# Get conversation history
def get_conversations(owner_id, conversation_type):
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("conversation_type", conversation_type)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data


# Get messages from a conversation
def get_messages(conversation_id):
    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )

    return result.data


# Delete a conversation and its messages
def delete_conversation(conversation_id):
    result = (
        supabase.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .execute()
    )

    return result.data
