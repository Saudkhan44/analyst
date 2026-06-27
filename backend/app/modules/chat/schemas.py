"""
Chat schemas using Pydantic v2.

Request and response models for chat operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class ChatMessageRequest(BaseModel):
    """Chat message request."""

    dataset_id: UUID = Field(..., description="Dataset ID to chat about")
    message: str = Field(..., min_length=1, description="User message")


class ChatMessageSchema(BaseModel):
    """Chat message schema."""

    id: UUID = Field(..., description="Message ID")
    session_id: UUID = Field(..., description="Session ID")
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    message: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response."""

    dataset_id: UUID = Field(..., description="Dataset ID")
    session_id: UUID = Field(..., description="Session ID")
    messages: List[ChatMessageSchema] = Field(..., description="Chat messages")
    count: int = Field(..., ge=0, description="Total messages")


class ChatResponseMessage(BaseModel):
    """Response from chat endpoint."""

    session_id: UUID = Field(..., description="Session ID")
    message: str = Field(..., description="Assistant response")
    created_at: datetime = Field(..., description="Creation timestamp")
