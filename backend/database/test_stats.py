from backend.database.stats import save_stats, get_latest_stats

save_stats(1200, 2, 1, 0)

stats = get_latest_stats()

print("Latest stats:", stats)