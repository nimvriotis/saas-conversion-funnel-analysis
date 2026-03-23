import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# =========================
# Configuration
# =========================
n_users = 20000
extra_visitors = 12000   # visitors who never sign up, so Visit > Sign Up

countries = [
    "United States",
    "United Kingdom",
    "Germany",
    "France",
    "Spain",
    "Netherlands",
    "Canada",
    "Australia"
]

devices = ["Desktop", "Mobile", "Tablet"]
channels = ["Organic Search", "Paid Search", "Facebook Ads", "Referral", "Direct", "Email Campaign"]
plans = ["Free", "Pro", "Family"]

start_date = datetime(2024, 1, 1)

# More realistic, intentionally uneven distributions
country_weights = np.array([0.24, 0.15, 0.14, 0.11, 0.10, 0.07, 0.11, 0.08])
device_weights = np.array([0.46, 0.38, 0.16])
channel_weights = np.array([0.16, 0.13, 0.08, 0.12, 0.11, 0.40])
plan_weights = np.array([0.62, 0.26, 0.12])

# Base funnel probabilities for signed-up users
base_email_verified = 0.78
base_trial_started = 0.70
base_onboarding_completed = 0.83
base_first_key_action = 0.79
base_subscription_started = 0.54

# Conversion adjustments by segment
channel_adjustments = {
    "Email Campaign": 1.20,
    "Referral": 1.12,
    "Organic Search": 1.05,
    "Direct": 0.98,
    "Paid Search": 0.92,
    "Facebook Ads": 0.82
}

device_adjustments = {
    "Desktop": 1.08,
    "Mobile": 0.97,
    "Tablet": 0.90
}

country_adjustments = {
    "United States": 1.10,
    "United Kingdom": 1.06,
    "Germany": 1.03,
    "France": 0.98,
    "Spain": 0.95,
    "Netherlands": 1.01,
    "Canada": 1.05,
    "Australia": 1.04
}


def weighted_choice(options, weights):
    return np.random.choice(options, p=weights)


def clamp(x, low=0.01, high=0.99):
    return max(low, min(high, x))


# =========================
# 1. Create signed-up users table
# =========================
users = []

for i in range(n_users):
    signup = start_date + timedelta(days=random.randint(0, 730))

    country = weighted_choice(countries, country_weights)
    device = weighted_choice(devices, device_weights)
    channel = weighted_choice(channels, channel_weights)
    plan = weighted_choice(plans, plan_weights)

    users.append({
        "user_id": f"U{i+1:06}",
        "signup_date": signup.strftime("%Y-%m-%d"),
        "country": country,
        "device_type": device,
        "acquisition_channel": channel,
        "plan_interest": plan
    })

users_df = pd.DataFrame(users)

# =========================
# 2. Create events table
# =========================
events = []
event_id = 1

# 2A. Add visits for users who eventually signed up
for _, u in users_df.iterrows():
    uid = u["user_id"]
    signup = datetime.strptime(u["signup_date"], "%Y-%m-%d")

    visit_time = signup - timedelta(
        days=random.randint(0, 7),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    events.append({
        "event_id": f"E{event_id:07}",
        "user_id": uid,
        "event_datetime": visit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": "Visit"
    })
    event_id += 1

# 2B. Add extra visitors who never sign up
for i in range(extra_visitors):
    visitor_id = f"V{i+1:06}"
    visit_time = start_date + timedelta(
        days=random.randint(0, 730),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    events.append({
        "event_id": f"E{event_id:07}",
        "user_id": visitor_id,
        "event_datetime": visit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": "Visit"
    })
    event_id += 1

# 2C. Add funnel events only for actual signed-up users
for _, u in users_df.iterrows():
    uid = u["user_id"]
    signup = datetime.strptime(u["signup_date"], "%Y-%m-%d")

    country = u["country"]
    device = u["device_type"]
    channel = u["acquisition_channel"]

    multiplier = (
        channel_adjustments[channel]
        * device_adjustments[device]
        * country_adjustments[country]
    )

    p_email_verified = clamp(base_email_verified * multiplier)
    p_trial_started = clamp(base_trial_started * multiplier)
    p_onboarding_completed = clamp(base_onboarding_completed * multiplier)
    p_first_key_action = clamp(base_first_key_action * multiplier)
    p_subscription_started = clamp(base_subscription_started * multiplier)

    # Sign Up event always exists for users table members
    current_time = signup + timedelta(hours=random.randint(1, 12))
    events.append({
        "event_id": f"E{event_id:07}",
        "user_id": uid,
        "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": "Sign Up"
    })
    event_id += 1

    # Email Verified
    if random.random() <= p_email_verified:
        current_time += timedelta(hours=random.randint(2, 48))
        events.append({
            "event_id": f"E{event_id:07}",
            "user_id": uid,
            "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "Email Verified"
        })
        event_id += 1
    else:
        continue

    # Trial Started
    if random.random() <= p_trial_started:
        current_time += timedelta(hours=random.randint(4, 72))
        events.append({
            "event_id": f"E{event_id:07}",
            "user_id": uid,
            "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "Trial Started"
        })
        event_id += 1
    else:
        continue

    # Onboarding Completed
    if random.random() <= p_onboarding_completed:
        current_time += timedelta(hours=random.randint(6, 96))
        events.append({
            "event_id": f"E{event_id:07}",
            "user_id": uid,
            "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "Onboarding Completed"
        })
        event_id += 1
    else:
        continue

    # First Key Action
    if random.random() <= p_first_key_action:
        current_time += timedelta(hours=random.randint(6, 120))
        events.append({
            "event_id": f"E{event_id:07}",
            "user_id": uid,
            "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "First Key Action"
        })
        event_id += 1
    else:
        continue

    # Subscription Started
    if random.random() <= p_subscription_started:
        current_time += timedelta(days=random.randint(1, 30), hours=random.randint(1, 12))
        events.append({
            "event_id": f"E{event_id:07}",
            "user_id": uid,
            "event_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "Subscription Started"
        })
        event_id += 1

events_df = pd.DataFrame(events)

# =========================
# 3. Create subscriptions table
# =========================
subs = []
sub_id = 1

subs_users = events_df.loc[events_df["event_type"] == "Subscription Started", "user_id"].unique()

users_lookup = users_df.set_index("user_id")
subscription_event_lookup = (
    events_df[events_df["event_type"] == "Subscription Started"]
    .sort_values("event_datetime")
    .drop_duplicates("user_id")
    .set_index("user_id")
)

for uid in subs_users:
    signup_date = datetime.strptime(users_lookup.loc[uid, "signup_date"], "%Y-%m-%d")
    subscription_event_date = datetime.strptime(
        subscription_event_lookup.loc[uid, "event_datetime"],
        "%Y-%m-%d %H:%M:%S"
    )

    plan_interest = users_lookup.loc[uid, "plan_interest"]

    if plan_interest == "Family":
        plan_tier = np.random.choice(["Family", "Pro"], p=[0.75, 0.25])
    elif plan_interest == "Pro":
        plan_tier = np.random.choice(["Pro", "Family"], p=[0.85, 0.15])
    else:
        plan_tier = np.random.choice(["Pro", "Family"], p=[0.70, 0.30])

    billing_cycle = np.random.choice(["Monthly", "Annual"], p=[0.72, 0.28])

    if plan_tier == "Pro":
        monthly_revenue = np.random.choice([12.99, 14.99, 19.99], p=[0.25, 0.45, 0.30])
    else:
        monthly_revenue = np.random.choice([19.99, 24.99, 29.99], p=[0.25, 0.40, 0.35])

    # Always after signup, usually same day or after subscription event
    start = max(
        signup_date + timedelta(days=1),
        subscription_event_date + timedelta(days=random.randint(0, 3))
    )

    subs.append({
        "subscription_id": f"S{sub_id:06}",
        "user_id": uid,
        "subscription_start_date": start.strftime("%Y-%m-%d"),
        "plan_tier": plan_tier,
        "monthly_revenue": monthly_revenue,
        "billing_cycle": billing_cycle,
        "is_active": random.choice([True, False])
    })

    sub_id += 1

subs_df = pd.DataFrame(subs)

# =========================
# 4. Save exactly same file names
# =========================
users_df.to_csv("saas_users.csv", index=False)
events_df.to_csv("saas_events.csv", index=False)
subs_df.to_csv("saas_subscriptions.csv", index=False)

# =========================
# 5. Quick checks
# =========================
event_counts = events_df["event_type"].value_counts()

print("Dataset created successfully")
print("Files generated:")
print("saas_users.csv")
print("saas_events.csv")
print("saas_subscriptions.csv")
print()
print("Event counts:")
print(event_counts)
print()
print("Users table rows:", len(users_df))
print("Events table rows:", len(events_df))
print("Subscriptions table rows:", len(subs_df))