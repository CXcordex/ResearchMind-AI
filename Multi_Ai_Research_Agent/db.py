import os
import json
from supabase import create_client, Client
from passlib.context import CryptContext
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Hashing context
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

_supabase_client: Client = None

def get_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        # 1. Try environment variables (Local / Docker / Standard Cloud)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        # 2. Try Streamlit Secrets (Streamlit Community Cloud)
        if not url or not key:
            try:
                import streamlit as st
                url = st.secrets.get("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_KEY")
            except Exception:
                pass
        
        # 3. Last ditch: reload .env
        if not url or not key:
            load_dotenv()
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
        
        if url and key:
            try:
                _supabase_client = create_client(url, key)
            except Exception as e:
                print(f"[DB] Error creating Supabase client: {e}")
                return None
        else:
            print("[DB] Critical: SUPABASE_URL or SUPABASE_KEY missing in environment/secrets.")
            return None
    return _supabase_client

def init_db():
    client = get_client()
    if not client:
        print("[DB] Critical: Supabase client not initialized.")
        return
    print("[DB] Supabase integration active.")

# ── Auth ──
def create_user(email, full_name, password):
    client = get_client()
    if not client: raise RuntimeError("Database not initialized")
    
    h = pwd_ctx.hash(password)
    data = {
        "email": email.lower(),
        "full_name": full_name,
        "password_hash": h
    }
    client.table("users").insert(data).execute()

def verify_login(email, password) -> dict | None:
    client = get_client()
    if not client: 
        print("[DB] verify_login failure: client is None")
        return None
        
    res = client.table("users").select("*").eq("email", email.lower()).execute()
    if not res.data:
        return None
    
    user = res.data[0]
    try:
        if pwd_ctx.verify(password, user["password_hash"]):
            return user
    except Exception:
        return None
    return None

# ── Research ──
def save_research(user_id, topic, queries, sources, evidence, report, elapsed, model, temp):
    client = get_client()
    if not client: return
    
    data = {
        "user_id": user_id,
        "topic": topic,
        "queries": queries,
        "sources": sources,
        "evidence": evidence,
        "report": report,
        "elapsed_sec": elapsed,
        "model_used": model,
        "temperature": temp
    }
    client.table("research_sessions").insert(data).execute()

def get_latest_research(user_id) -> dict | None:
    client = get_client()
    if not client: return None
    
    res = client.table("research_sessions") \
        .select("topic,report,sources,evidence") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    return res.data[0] if res.data else None

# ── Document ──
def save_document(user_id, filename, file_size_kb, mime, full_text, summary,
                  key_findings, key_topics, metadata_info, question, answer, model):
    client = get_client()
    if not client: return
    
    data = {
        "user_id": user_id,
        "filename": filename,
        "file_size_kb": file_size_kb,
        "mime_type": mime,
        "full_text": full_text[:8000],
        "summary": summary,
        "key_findings": key_findings,
        "key_topics": key_topics,
        "metadata_info": metadata_info,
        "question": question,
        "answer": answer,
        "model_used": model
    }
    client.table("document_sessions").insert(data).execute()

def get_latest_document(user_id) -> dict | None:
    client = get_client()
    if not client: return None
    
    res = client.table("document_sessions") \
        .select("filename,full_text,summary,key_findings") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    return res.data[0] if res.data else None

# ── Chat ──
def save_chat_msg(user_id, role, content, session_tag):
    client = get_client()
    if not client: return
    
    data = {
        "user_id": user_id,
        "role": role,
        "content": content,
        "session_tag": session_tag
    }
    client.table("chat_history").insert(data).execute()

def get_chat_history(user_id, session_tag, limit=12) -> list:
    client = get_client()
    if not client: return []
    
    res = client.table("chat_history") \
        .select("role,content") \
        .eq("user_id", user_id) \
        .eq("session_tag", session_tag) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return list(reversed(res.data))
