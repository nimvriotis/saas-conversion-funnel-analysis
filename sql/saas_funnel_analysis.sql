-- SaaS Conversion Funnel Analysis
-- Author: Georgios Nimvriotis

-- Create database
DROP SCHEMA IF EXISTS saas_funnel;
CREATE SCHEMA saas_funnel;
USE saas_funnel;

-- Users table
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    signup_date DATE,
    country VARCHAR(50),
    device_type VARCHAR(50),
    acquisition_channel VARCHAR(50),
    plan_interest VARCHAR(50)
);

-- Events table
CREATE TABLE user_events (
    event_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    event_datetime DATETIME,
    event_type VARCHAR(100)
);

-- Subscriptions table
CREATE TABLE subscriptions (
    subscription_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    subscription_start_date DATE,
    plan_tier VARCHAR(50),
    monthly_revenue DECIMAL(10,2),
    billing_cycle VARCHAR(20),
    is_active VARCHAR(10),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Funnel Stage Distribution
SELECT
    event_type,
    COUNT(DISTINCT user_id) AS users_reached_stage
FROM user_events
GROUP BY event_type
ORDER BY
CASE
    WHEN event_type = 'Visit' THEN 1
    WHEN event_type = 'Sign Up' THEN 2
    WHEN event_type = 'Email Verified' THEN 3
    WHEN event_type = 'Trial Started' THEN 4
    WHEN event_type = 'Onboarding Completed' THEN 5
    WHEN event_type = 'First Key Action' THEN 6
    WHEN event_type = 'Subscription Started' THEN 7
END;

-- Conversion Rate Between Funnel Stages
WITH stage_counts AS (
    SELECT 'Visit' AS stage_name, 1 AS stage_order, COUNT(DISTINCT user_id) AS users_count
    FROM user_events
    WHERE event_type = 'Visit'

    UNION ALL
    SELECT 'Sign Up', 2, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Sign Up'

    UNION ALL
    SELECT 'Email Verified', 3, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Email Verified'

    UNION ALL
    SELECT 'Trial Started', 4, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Trial Started'

    UNION ALL
    SELECT 'Onboarding Completed', 5, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Onboarding Completed'

    UNION ALL
    SELECT 'First Key Action', 6, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'First Key Action'

    UNION ALL
    SELECT 'Subscription Started', 7, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Subscription Started'
)
SELECT
    stage_name,
    users_count,
    LAG(users_count) OVER (ORDER BY stage_order) AS previous_stage_count,
    ROUND(
        users_count * 100.0 / LAG(users_count) OVER (ORDER BY stage_order),
        2
    ) AS conversion_from_previous_stage_pct
FROM stage_counts
ORDER BY stage_order;

-- Drop-Off Analysis Between Funnel Stages
WITH stage_counts AS (
    SELECT 'Visit' AS stage_name, 1 AS stage_order, COUNT(DISTINCT user_id) AS users_count
    FROM user_events
    WHERE event_type = 'Visit'

    UNION ALL
    SELECT 'Sign Up', 2, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Sign Up'

    UNION ALL
    SELECT 'Email Verified', 3, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Email Verified'

    UNION ALL
    SELECT 'Trial Started', 4, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Trial Started'

    UNION ALL
    SELECT 'Onboarding Completed', 5, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Onboarding Completed'

    UNION ALL
    SELECT 'First Key Action', 6, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'First Key Action'

    UNION ALL
    SELECT 'Subscription Started', 7, COUNT(DISTINCT user_id)
    FROM user_events
    WHERE event_type = 'Subscription Started'
)
SELECT
    stage_name,
    users_count,
    LEAD(users_count) OVER (ORDER BY stage_order) AS next_stage_users,
    users_count - LEAD(users_count) OVER (ORDER BY stage_order) AS drop_off_users,
    ROUND(
        (users_count - LEAD(users_count) OVER (ORDER BY stage_order)) * 100.0 / users_count,
        2
    ) AS drop_off_rate_pct
FROM stage_counts
ORDER BY stage_order;

-- Conversion to Subscription by Acquisition Channel
SELECT
    u.acquisition_channel,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT s.user_id) AS subscribers,
    ROUND(
        COUNT(DISTINCT s.user_id) * 100.0 / COUNT(DISTINCT u.user_id),
        2
    ) AS conversion_to_subscription_pct
FROM users u
LEFT JOIN subscriptions s
    ON u.user_id = s.user_id
GROUP BY u.acquisition_channel
ORDER BY conversion_to_subscription_pct DESC;

-- Conversion to Subscription by Device Type
SELECT
    u.device_type,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT s.user_id) AS subscribers,
    ROUND(
        COUNT(DISTINCT s.user_id) * 100.0 / COUNT(DISTINCT u.user_id),
        2
    ) AS conversion_to_subscription_pct
FROM users u
LEFT JOIN subscriptions s
    ON u.user_id = s.user_id
GROUP BY u.device_type
ORDER BY conversion_to_subscription_pct DESC;

-- Conversion to Subscription by Country
SELECT
    u.country,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT s.user_id) AS subscribers,
    ROUND(
        COUNT(DISTINCT s.user_id) * 100.0 / COUNT(DISTINCT u.user_id),
        2
    ) AS conversion_to_subscription_pct
FROM users u
LEFT JOIN subscriptions s
    ON u.user_id = s.user_id
GROUP BY u.country
ORDER BY conversion_to_subscription_pct DESC, total_users DESC;

-- Revenue by Plan Tier and Billing Cycle
SELECT
    plan_tier,
    billing_cycle,
    COUNT(DISTINCT user_id) AS subscribers,
    ROUND(SUM(monthly_revenue), 2) AS total_monthly_revenue
FROM subscriptions
GROUP BY plan_tier, billing_cycle
ORDER BY total_monthly_revenue DESC;

-- Data Quality Check: subscriptions earlier than signup
SELECT
    SUM(CASE WHEN s.subscription_start_date < u.signup_date THEN 1 ELSE 0 END) AS invalid_rows,
    COUNT(*) AS total_rows
FROM users u
JOIN subscriptions s
    ON u.user_id = s.user_id;