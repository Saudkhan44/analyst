"""
Chat service layer.

Handles business logic for chat operations and AI interactions.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.core.database import ChatSession, ChatMessage, Dataset, Dashboard
from app.shared.ai_client import AIClient

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations."""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClient()

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    def get_or_create_session(
        self,
        dataset_id: str,
        user_id: str,
    ) -> ChatSession:

        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.dataset_id == dataset_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )

        if session:
            return session

        session = ChatSession(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created chat session: {session.id}")

        return session

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def get_session_messages(
        self,
        session_id: str,
    ) -> List[ChatMessage]:

        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------
    # Dashboard Context
    # ------------------------------------------------------------------

    def get_dashboard_context(
        self,
        dataset_id: str,
    ) -> Dict[str, Any]:

        dashboard = (
            self.db.query(Dashboard)
            .filter(Dashboard.dataset_id == dataset_id)
            .first()
        )

        if not dashboard:
            return {}

        return {
            "summary": dashboard.summary,
            "charts": dashboard.charts,
        }

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    async def send_message(
        self,
        dataset_id: str,
        user_id: str,
        user_message: str,
    ) -> str:

        # --------------------------------------------------------------
        # Verify dataset
        # --------------------------------------------------------------

        dataset = (
            self.db.query(Dataset)
            .filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id,
            )
            .first()
        )

        if not dataset:
            raise ValueError("Dataset not found")

        # --------------------------------------------------------------
        # Session
        # --------------------------------------------------------------

        session = self.get_or_create_session(
            dataset_id,
            user_id,
        )

        # --------------------------------------------------------------
        # Previous conversation
        # --------------------------------------------------------------

        history = self.get_session_messages(session.id)

        previous_messages = [
            {
                "role": msg.role,
                "content": msg.message,
            }
            for msg in history
        ]

        # --------------------------------------------------------------
        # Dashboard Context
        # --------------------------------------------------------------

        dashboard_context = self.get_dashboard_context(dataset_id)

        # --------------------------------------------------------------
        # Build Prompt
        # --------------------------------------------------------------

        messages = self.ai_client.build_context_prompt(
            question=user_message,
            dashboard_summary=dashboard_context,
            previous_messages=previous_messages,
        )

        # --------------------------------------------------------------
        # AI CALL
        # --------------------------------------------------------------

        ai_response = self.ai_client.chat(messages)

        # --------------------------------------------------------------
        # Save BOTH messages in ONE transaction
        # --------------------------------------------------------------

        try:

            user_msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session.id,
                role="user",
                message=user_message,
                created_at=datetime.utcnow(),
            )

            assistant_msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session.id,
                role="assistant",
                message=ai_response,
                created_at=datetime.utcnow(),
            )

            self.db.add(user_msg)
            self.db.add(assistant_msg)

            self.db.commit()

            logger.info(
                f"Chat completed successfully for session {session.id}"
            )

            return ai_response

        except Exception:

            self.db.rollback()
            logger.exception("Failed to save chat messages")

            raise

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_chat_history(
        self,
        dataset_id: str,
        user_id: str,
    ) -> Optional[ChatSession]:

        return (
            self.db.query(ChatSession)
            .filter(
                ChatSession.dataset_id == dataset_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_session(
        self,
        session_id: str,
        user_id: str,
    ) -> bool:

        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            return False

        try:

            (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .delete(synchronize_session=False)
            )

            self.db.delete(session)

            self.db.commit()

            logger.info(f"Deleted chat session {session_id}")

            return True

        except Exception:

            self.db.rollback()
            logger.exception("Failed to delete session")

            raise