import psycopg2

def get_connection():
    # Connects Python to PostgreSQL
    return psycopg2.connect(
        dbname="ace_database",
        user="postgres",
        password="Timnpw4DB",
        host="localhost",
        port="5432"
    )

def create_tables():
    # Creates table if it does not already exist
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            id SERIAL PRIMARY KEY,
            player_name TEXT NOT NULL,
            chips INTEGER NOT NULL,
            wins INTEGER NOT NULL,
            losses INTEGER NOT NULL,
            pushes INTEGER NOT NULL,
            games_played INTEGER NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()