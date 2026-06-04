from backend.database.stats import save_stats, get_latest_stats

save_stats(
    "Cisco",
    3500,
    10,
    3,
    2,
    1
)

print(get_latest_stats())