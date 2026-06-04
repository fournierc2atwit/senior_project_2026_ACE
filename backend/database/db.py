import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Connects Python to Neon/PostgreSQL using DATABASE_URL from .env
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL was not found. Check your .env file.")

    return psycopg2.connect(database_url)

def create_tables():
    # Creates table if it does not already exist
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id SERIAL PRIMARY KEY,
            player_name TEXT NOT NULL UNIQUE,
            chips INTEGER NOT NULL,
            wins INTEGER NOT NULL,
            losses INTEGER NOT NULL,
            pushes INTEGER NOT NULL,
            games_played INTEGER NOT NULL,
            bankrupts INTEGER NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()