# migrate_db.py - Database migration script
import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate the existing database to add new columns and tables"""
    
    # Path to the database
    db_path = "app.db"
    
    print("Starting database migration...")
    
    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if sessions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        sessions_table_exists = cursor.fetchone() is not None
        
        if not sessions_table_exists:
            print("Sessions table not found. Database will be created by SQLAlchemy on startup.")
            return
        
        # Check if sessions table has the new columns
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns to sessions table if they don't exist
        if 'updated_at' not in columns:
            print("Adding updated_at column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        if 'title' not in columns:
            print("Adding title column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN title VARCHAR(255)")
        
        # Create new tables
        print("Creating conversation_history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id VARCHAR(80) PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                message_id VARCHAR(80) NOT NULL,
                user_query TEXT NOT NULL,
                ai_response TEXT,
                generated_code TEXT,
                sandbox_url VARCHAR(500),
                generation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_edit BOOLEAN DEFAULT 0,
                meta JSON,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        """)
        
        print("Creating session_generated_links table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_generated_links (
                id VARCHAR(80) PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                conversation_id VARCHAR(80) NOT NULL,
                sandbox_url VARCHAR(500) NOT NULL,
                generated_code TEXT NOT NULL,
                generation_number INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                meta JSON,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (conversation_id) REFERENCES conversation_history (id)
            )
        """)
        
        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_session_id ON conversation_history (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_history_message_id ON conversation_history (message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_generated_links_session_id ON session_generated_links (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_generated_links_conversation_id ON session_generated_links (conversation_id)")
        
        # Update existing sessions to have updated_at = created_at
        print("Updating existing sessions...")
        cursor.execute("UPDATE sessions SET updated_at = created_at WHERE updated_at IS NULL")
        
        # Commit all changes
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
