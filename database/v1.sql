-- v1.sql: Initial schema for Shell Copilot database

drop table if exists chats;
drop table if exists sessions;

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(36) PRIMARY KEY,            
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
    is_active BOOLEAN DEFAULT TRUE                          
);


-- Create chats table to store message exchanges
CREATE TABLE IF NOT EXISTS chats (
    chat_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT,
    intent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);


