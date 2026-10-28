"""Defime Request / Response DTOs for Agent and RAG Module
"""
from pydantic import BaseModel

# ============================================================
# AGENT  Schemas
# ============================================================

class AuditRequest(BaseModel):
    """Agent Audit Request DTO

    Args:
        BaseModel (_type_): _description_
    """
    request_text: str

class AuditResponse(BaseModel):
    """Agent Audit Run Response DTO

    Args:
        BaseModel (_type_): _description_
    """
    risk_result: str
    tax_result: str
    control_result: str
    cfo_memo: str

# ============================================================
# RAG  Schemas
# ============================================================


class QueryRequest(BaseModel):
    """RAG Request DTO

    Args:
        BaseModel (_type_): _description_
    """
    query: str
    retriever_type: str = "similarity"

class QueryResponse(BaseModel):
    """RAG Response DTO

    Args:
        BaseModel (_type_): _description_
    """
    answer: str
