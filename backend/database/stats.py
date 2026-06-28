from backend.database.db import get_connection

_DB_AVAILABLE = True
_IN_MEMORY_PLAYER_STATS = {}
_IN_MEMORY_SLOTS_STATS = {}

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

def save_slot_spin(player_name, amount, total_return, payout, won):
    player_name = _normalize_player_name(player_name)

    slot_win = 1 if won else 0
    slot_loss = 0 if won else 1

    if not _DB_AVAILABLE:
        current = _IN_MEMORY_SLOTS_STATS.get(player_name, {
            "player_name": player_name,
            "spins": 0,
            "wins": 0,
            "losses": 0,
            "total_wagered": 0,
            "total_payout": 0,
            "biggest_win": 0,
        })

        current["spins"] += 1
        current["wins"] += slot_win
        current["losses"] += slot_loss
        current["total_wagered"] += amount
        current["total_payout"] += total_return
        current["biggest_win"] = max(current["biggest_win"], payout)

        _IN_MEMORY_SLOTS_STATS[player_name] = current
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO slots_stats
        (player_name, spins, wins, losses, total_wagered, total_payout, biggest_win)
        VALUES (%s, 1, %s, %s, %s, %s, %s)
        ON CONFLICT (player_name)
        DO UPDATE SET
            spins = slots_stats.spins + 1,
            wins = slots_stats.wins + EXCLUDED.wins,
            losses = slots_stats.losses + EXCLUDED.losses,
            total_wagered = slots_stats.total_wagered + EXCLUDED.total_wagered,
            total_payout = slots_stats.total_payout + EXCLUDED.total_payout,
            biggest_win = GREATEST(slots_stats.biggest_win, EXCLUDED.biggest_win);
    """, (player_name, slot_win, slot_loss, amount, total_return, payout))

    conn.commit()
    cur.close()
    conn.close()


def get_slots_stats(player_name):
    player_name = _normalize_player_name(player_name)

    if not _DB_AVAILABLE:
        stats = _IN_MEMORY_SLOTS_STATS.get(player_name)

        if not stats:
            return None

        return (
            stats["player_name"],
            stats["spins"],
            stats["wins"],
            stats["losses"],
            stats["total_wagered"],
            stats["total_payout"],
            stats["biggest_win"],
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT player_name, spins, wins, losses, total_wagered, total_payout, biggest_win
        FROM slots_stats
        WHERE LOWER(player_name) = LOWER(%s);
    """, (player_name,))

    stats = cur.fetchone()

    cur.close()
    conn.close()

    return stats