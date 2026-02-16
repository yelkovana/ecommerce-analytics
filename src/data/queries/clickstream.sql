-- Clickstream queries with Jinja2 templating

{% if query_type == 'session_metrics' %}
SELECT
    {% if segment %}{{ segment }} AS segment,{% endif %}
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT user_id) AS users,
    AVG(pages_in_session) AS pages_per_session,
    AVG(session_duration_seconds) AS avg_session_duration,
    SAFE_DIVIDE(
        COUNTIF(pages_in_session = 1),
        COUNT(DISTINCT session_id)
    ) AS bounce_rate
FROM (
    SELECT
        session_id,
        user_id,
        {% if segment %}{{ segment }},{% endif %}
        COUNT(*) AS pages_in_session,
        TIMESTAMP_DIFF(MAX(event_timestamp), MIN(event_timestamp), SECOND) AS session_duration_seconds
    FROM `{{ dataset }}.clickstream_events`
    WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    GROUP BY session_id, user_id{% if segment %}, {{ segment }}{% endif %}
)
{% if segment %}GROUP BY segment{% endif %}

{% elif query_type == 'funnel' %}
WITH funnel_events AS (
    SELECT
        session_id,
        user_id,
        event_name,
        MIN(event_timestamp) AS first_event_time
    FROM `{{ dataset }}.clickstream_events`
    WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
      AND event_name IN ({{ funnel_steps | map('tojson') | join(', ') }})
    GROUP BY session_id, user_id, event_name
)
SELECT
    event_name AS step,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT user_id) AS users
FROM funnel_events
GROUP BY event_name
ORDER BY
    CASE event_name
        {% for step in funnel_steps %}
        WHEN '{{ step }}' THEN {{ loop.index }}
        {% endfor %}
    END

{% elif query_type == 'traffic_sources' %}
SELECT
    traffic_source,
    traffic_medium,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT user_id) AS users,
    SAFE_DIVIDE(
        COUNTIF(pages_in_session = 1),
        COUNT(DISTINCT session_id)
    ) AS bounce_rate
FROM (
    SELECT
        session_id,
        user_id,
        traffic_source,
        traffic_medium,
        COUNT(*) OVER (PARTITION BY session_id) AS pages_in_session
    FROM `{{ dataset }}.clickstream_events`
    WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
)
GROUP BY traffic_source, traffic_medium
ORDER BY sessions DESC

{% elif query_type == 'traffic_sources_with_conversions' %}
WITH sessions AS (
    SELECT
        session_id,
        ANY_VALUE(traffic_source) AS traffic_source,
        ANY_VALUE(traffic_medium) AS traffic_medium
    FROM `{{ dataset }}.clickstream_events`
    WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    GROUP BY session_id
),
order_sessions AS (
    SELECT DISTINCT session_id, SUM(order_total) AS revenue
    FROM `{{ dataset }}.orders`
    WHERE DATE(order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
    GROUP BY session_id
)
SELECT
    s.traffic_source,
    s.traffic_medium,
    COUNT(DISTINCT s.session_id) AS sessions,
    COUNT(DISTINCT o.session_id) AS conversions,
    SAFE_DIVIDE(COUNT(DISTINCT o.session_id), COUNT(DISTINCT s.session_id)) AS conversion_rate,
    COALESCE(SUM(o.revenue), 0) AS revenue
FROM sessions s
LEFT JOIN order_sessions o USING (session_id)
GROUP BY s.traffic_source, s.traffic_medium
ORDER BY sessions DESC

{% elif query_type == 'device_segmentation' %}
SELECT
    device_category,
    browser,
    os,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT user_id) AS users,
    AVG(pages_in_session) AS pages_per_session,
    AVG(session_duration_seconds) AS avg_session_duration
FROM (
    SELECT
        session_id,
        user_id,
        device_category,
        browser,
        os,
        COUNT(*) OVER (PARTITION BY session_id) AS pages_in_session,
        TIMESTAMP_DIFF(
            MAX(event_timestamp) OVER (PARTITION BY session_id),
            MIN(event_timestamp) OVER (PARTITION BY session_id),
            SECOND
        ) AS session_duration_seconds
    FROM `{{ dataset }}.clickstream_events`
    WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
)
GROUP BY device_category, browser, os
ORDER BY sessions DESC

{% elif query_type == 'page_engagement' %}
SELECT
    page_path,
    COUNT(*) AS pageviews,
    COUNT(DISTINCT session_id) AS unique_pageviews,
    AVG(time_on_page) AS avg_time_on_page,
    AVG(scroll_depth) AS avg_scroll_depth,
    SAFE_DIVIDE(
        COUNTIF(is_exit),
        COUNT(*)
    ) AS exit_rate
FROM `{{ dataset }}.clickstream_events`
WHERE DATE(event_timestamp) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY page_path
ORDER BY pageviews DESC
LIMIT {{ limit | default(100) }}

{% endif %}
