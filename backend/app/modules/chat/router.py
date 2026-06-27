"""
Chat API routes.

Endpoints for dataset chat and AI interactions.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.modules.auth.dependencies import get_current_user
from app.modules.chat.service import ChatService
from app.modules.chat.schemas import (
    ChatMessageRequest,
    ChatHistoryResponse,
    ChatResponseMessage,
    ChatMessageSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponseMessage, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponseMessage:
    """
    Send message to AI about dataset.

    Creates or retrieves chat session for dataset and sends message to Groq.

    Args:
        request: Chat message request
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatResponseMessage: AI response

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        service = ChatService(db)
        response = await service.send_message(
            dataset_id=str(request.dataset_id),
            user_id=str(current_user.user_id),
            user_message=request.message,
        )

        # Get the session
        session = service.get_chat_history(str(request.dataset_id), str(current_user.user_id))

        logger.info(f"Chat message sent by {current_user.email}")

        return ChatResponseMessage(
            session_id=session.id,
            message=response,
            created_at=session.created_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
      import traceback

      traceback.print_exc()

      raise HTTPException(
        status_code=500,
        detail=str(e),
    )

@router.get("/{dataset_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Get chat history for a dataset.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatHistoryResponse: Chat history with all messages

    Raises:
        HTTPException: If dataset or history not found
    """
    try:
        service = ChatService(db)
        session = service.get_chat_history(dataset_id, str(current_user.user_id))

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chat history found for this dataset",
            )

        # Get messages
        messages = service.get_session_messages(str(session.id))

        logger.info(f"Chat history retrieved by {current_user.email}: {dataset_id}")

        return ChatHistoryResponse(
            dataset_id=session.dataset_id,
            session_id=session.id,
            messages=[ChatMessageSchema.model_validate(msg) for msg in messages],
            count=len(messages),
        )

    except HTTPException:
        raise
    except Exception:
      import traceback
      traceback.print_exc()
      raise