# placeholder: bisa di-expand untuk Prometheus later
def format_stats_row(row):
    return {
        "received": row["received"],
        "unique_processed": row["unique_processed"],
        "duplicate_dropped": row["duplicate_dropped"],
        "started_at": str(row["started_at"])
    }