from backend.database.db import get_connection

def save_stats(player_name, chips, wins, losses, pushes, bankrupts):
    games_played = wins + losses + pushes

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO player_stats
        (player_name, chips, wins, losses, pushes, games_played, bankrupts)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_name)
        DO UPDATE SET
            chips = EXCLUDED.chips,
            wins = EXCLUDED.wins,
            losses = EXCLUDED.losses,
            pushes = EXCLUDED.pushes,
            games_played = EXCLUDED.games_played,
            bankrupts = EXCLUDED.bankrupts;
    """, (player_name, chips, wins, losses, pushes, games_played, bankrupts))
    
    conn.commit()
    cur.close()
    conn.close()

def get_latest_stats():
    conn = get_connection()
    cur = conn.cursor()

    # Gets the most recent stats saved
    cur.execute("""
        SELECT player_name, chips, wins, losses, pushes, games_played, bankrupts
        FROM player_stats
        ORDER BY id DESC
        LIMIT 1;
    """)

    stats = cur.fetchone()
    cur.close()
    conn.close()

    return stats

def get_player_stats(player_name):
    conn = get_connection()
    cur = conn.cursor()

    # Gets latest saved stats for this player
    cur.execute("""
        SELECT player_name, chips, wins, losses, pushes, games_played, bankrupts
        FROM player_stats
        WHERE LOWER(player_name) = LOWER(%s)
        ORDER BY id DESC
        LIMIT 1;
    """, (player_name,))

    stats = cur.fetchone()

    cur.close()
    conn.close()

    return stats
