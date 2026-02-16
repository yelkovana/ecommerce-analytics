-- Recommendation Engine queries

{% if query_type == 'engagement_metrics' %}
SELECT
    widget_id,
    algorithm,
    COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS clicks,
    COUNT(CASE WHEN event_type = 'atc' THEN 1 END) AS add_to_carts,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases
FROM `{{ dataset }}.recommendation_events`
WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY widget_id, algorithm

{% elif query_type == 'revenue_impact' %}
WITH rec_sessions AS (
    SELECT DISTINCT session_id, 1 AS has_rec_interaction
    FROM `{{ dataset }}.recommendation_events`
    WHERE event_type IN ('click', 'atc', 'purchase')
      AND DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
),
all_sessions AS (
    SELECT
        session_id,
        SUM(order_total) AS revenue,
        COUNT(DISTINCT order_id) AS orders,
        AVG(order_total) AS aov
    FROM `{{ dataset }}.orders`
    WHERE DATE(order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    GROUP BY session_id
)
SELECT
    COALESCE(r.has_rec_interaction, 0) AS interacted_with_recs,
    COUNT(DISTINCT a.session_id) AS sessions,
    SUM(a.revenue) AS revenue,
    AVG(a.revenue) AS avg_revenue_per_session,
    AVG(a.aov) AS aov,
    SUM(a.orders) AS orders
FROM all_sessions a
LEFT JOIN rec_sessions r ON a.session_id = r.session_id
GROUP BY interacted_with_recs

{% elif query_type == 'widget_comparison' %}
SELECT
    widget_id,
    COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS clicks,
    COUNT(CASE WHEN event_type = 'atc' THEN 1 END) AS add_to_carts,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'click' THEN session_id END) AS click_sessions
FROM `{{ dataset }}.recommendation_events`
WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY widget_id

{% elif query_type == 'algorithm_comparison' %}
SELECT
    algorithm,
    widget_id,
    COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS clicks,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases,
    COUNT(DISTINCT product_id) AS unique_products_shown
FROM `{{ dataset }}.recommendation_events`
WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY algorithm, widget_id

{% elif query_type == 'coverage_diversity' %}
SELECT
    product_id,
    COUNT(*) AS times_recommended,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS times_clicked,
    LOGICAL_OR(is_new_item) AS is_new_item
FROM `{{ dataset }}.recommendation_events`
WHERE event_type = 'impression'
  AND DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY product_id

{% elif query_type == 'cold_start' %}
SELECT
    is_new_user,
    is_new_item,
    COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
    COUNT(CASE WHEN event_type = 'click' THEN 1 END) AS clicks,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases
FROM `{{ dataset }}.recommendation_events`
WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY is_new_user, is_new_item

{% endif %}
