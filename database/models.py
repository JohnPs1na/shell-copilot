from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from database.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP



class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String(36), primary_key=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    last_active_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    is_active = Column(Boolean, nullable=False, default=True)
    

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    user_message = Column(String, nullable=False)
    assistant_response = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))