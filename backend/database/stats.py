from backend.database.db import get_connection

_DB_AVAILABLE = True
_IN_MEMORY_PLAYER_STATS = {}

try:
    conn = get_connection()
    conn.close()
except Exception:
    _DB_AVAILABLE = False


def _normalize_player_name(player_name):
    return player_name.strip().lower()


def save_stats(player_name, chips, wins, losses, pushes, bankrupts):
    player_name = _normalize_player_name(player_name)
    games_played = wins + losses + pushes

    if not _DB_AVAILABLE:
        _IN_MEMORY_PLAYER_STATS[player_name] = (
            player_name,
            chips,
            wins,
            losses,
            pushes,
            games_played,
            bankrupts,
        )
        return

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
    player_name = player_name.strip().lower()

    if not _DB_AVAILABLE:
        return _IN_MEMORY_PLAYER_STATS.get(player_name)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT player_name, chips, wins, losses, pushes, games_played, bankrupts
        FROM player_stats
        WHERE LOWER(player_name) = LOWER(%s)
    """, (player_name,))

    stats = cur.fetchone()

    cur.close()
    conn.close()

    return stats


def get_all_player_stats():
    if not _DB_AVAILABLE:
        return sorted(
            _IN_MEMORY_PLAYER_STATS.values(),
            key=lambda row: row[1],
            reverse=True,
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT player_name, chips, wins, losses, pushes,
               games_played, bankrupts
        FROM player_stats
        ORDER BY chips DESC;
    """)

    players = cur.fetchall()

    cur.close()
    conn.close()

    return players   
