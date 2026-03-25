"""generate_synthetic_data.py — Synthetic FitTrack event and user data generator.

Frozen snapshot from Module 0 output (prerequisite for Module 3).
Generates ~10k users and ~500k events for DAU/MAU analysis practice.

Usage:
    uv run python scripts/generate_synthetic_data.py

Environment variables:
    SYNTHETIC_NUM_USERS     Number of users to generate (default: 10000)
    SYNTHETIC_START_DATE    Event data start date (default: 2026-01-01)
    SYNTHETIC_END_DATE      Event data end date (default: 2026-03-31)
"""

import os
import uuid
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Configuration via environment variables
NUM_USERS = int(os.environ.get("SYNTHETIC_NUM_USERS", "10000"))
START_DATE = os.environ.get("SYNTHETIC_START_DATE", "2026-01-01")
END_DATE = os.environ.get("SYNTHETIC_END_DATE", "2026-03-31")

EVENT_TYPES = [
    "app_open",
    "screen_view",
    "workout_start",
    "workout_end",
    "profile_view",
    "settings_change",
    "notification_open",
    "share",
]

PLATFORMS = ["ios", "android"]
COUNTRIES = ["KR", "US", "JP", "GB", "DE", "FR", "CA", "AU"]
ACQUISITION_SOURCES = ["organic", "google_ads", "facebook", "instagram", "referral", "app_store"]


def generate_users(num_users: int, start_date: str) -> pd.DataFrame:
    """Generate synthetic user profiles."""
    rng = np.random.default_rng(42)
    start = datetime.strptime(start_date, "%Y-%m-%d")

    users = []
    for i in range(num_users):
        created_at = start - timedelta(days=rng.integers(0, 180))
        users.append(
            {
                "user_id": f"user_{i:06d}",
                "created_at": created_at.isoformat(),
                "country": rng.choice(COUNTRIES),
                "platform": rng.choice(PLATFORMS),
                "acquisition_source": rng.choice(ACQUISITION_SOURCES),
            }
        )

    return pd.DataFrame(users)


def generate_events(
    users_df: pd.DataFrame, start_date: str, end_date: str
) -> pd.DataFrame:
    """Generate synthetic app events for given users."""
    rng = np.random.default_rng(123)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days

    events = []
    for _, user in users_df.iterrows():
        # Each user has a random activity level
        avg_events_per_day = rng.exponential(0.8)
        active_days = rng.choice(total_days, size=min(int(total_days * 0.6), total_days), replace=False)

        for day_offset in active_days:
            event_date = start + timedelta(days=int(day_offset))
            num_events = max(1, int(rng.poisson(avg_events_per_day)))

            for _ in range(num_events):
                hour = rng.integers(6, 24)
                minute = rng.integers(0, 60)
                event_ts = event_date.replace(hour=int(hour), minute=int(minute))

                events.append(
                    {
                        "event_id": str(uuid.uuid4()),
                        "user_id": user["user_id"],
                        "event_type": rng.choice(EVENT_TYPES),
                        "event_timestamp": event_ts.isoformat(),
                        "platform": user["platform"],
                        "app_version": f"3.{rng.integers(0, 5)}.{rng.integers(0, 10)}",
                        "properties": "{}",
                    }
                )

    return pd.DataFrame(events)


if __name__ == "__main__":
    print(f"Generating {NUM_USERS} users...")
    users_df = generate_users(NUM_USERS, START_DATE)
    print(f"  Generated {len(users_df)} users")

    print(f"Generating events from {START_DATE} to {END_DATE}...")
    events_df = generate_events(users_df, START_DATE, END_DATE)
    print(f"  Generated {len(events_df)} events")

    # Save to CSV for BigQuery loading
    os.makedirs("data", exist_ok=True)
    users_df.to_csv("data/raw_users.csv", index=False)
    events_df.to_csv("data/raw_events.csv", index=False)
    print("Saved to data/raw_users.csv and data/raw_events.csv")
