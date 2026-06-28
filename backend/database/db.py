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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS slots_stats (
            id SERIAL PRIMARY KEY,
            player_name TEXT NOT NULL UNIQUE,
            spins INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            total_wagered INTEGER NOT NULL DEFAULT 0,
            total_payout INTEGER NOT NULL DEFAULT 0,
            biggest_win INTEGER NOT NULL DEFAULT 0
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS roulette_stats (
            id SERIAL PRIMARY KEY,
            player_name TEXT NOT NULL UNIQUE,
            spins INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            total_wagered INTEGER NOT NULL DEFAULT 0,
            total_payout INTEGER NOT NULL DEFAULT 0,
            biggest_win INTEGER NOT NULL DEFAULT 0,
            straight_bets INTEGER NOT NULL DEFAULT 0,
            color_bets INTEGER NOT NULL DEFAULT 0,
            parity_bets INTEGER NOT NULL DEFAULT 0,
            dozen_bets INTEGER NOT NULL DEFAULT 0
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()