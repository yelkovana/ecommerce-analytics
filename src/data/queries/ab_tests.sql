-- A/B Test queries

{% if query_type == 'test_list' %}
SELECT
    test_id,
    test_name,
    start_date,
    end_date,
    status,
    hypothesis,
    primary_metric,
    allocation_ratio
FROM `{{ dataset }}.ab_tests`
{% if status %}WHERE status = '{{ status }}'{% endif %}
ORDER BY start_date DESC

{% elif query_type == 'test_assignments' %}
SELECT
    user_id,
    variant,
    device,
    traffic_source,
    user_type
FROM `{{ dataset }}.ab_test_assignments`
WHERE test_id = '{{ test_id }}'

{% elif query_type == 'test_metrics' %}
SELECT
    user_id,
    variant,
    metric_date,
    converted,
    revenue,
    pre_experiment_revenue,
    pre_experiment_sessions
FROM `{{ dataset }}.ab_test_metrics`
WHERE test_id = '{{ test_id }}'
ORDER BY metric_date

{% elif query_type == 'test_summary' %}
SELECT
    variant,
    COUNT(DISTINCT user_id) AS users,
    SUM(converted) AS conversions,
    AVG(converted) AS conversion_rate,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS avg_revenue,
    STDDEV(revenue) AS std_revenue
FROM `{{ dataset }}.ab_test_metrics`
WHERE test_id = '{{ test_id }}'
GROUP BY variant

{% elif query_type == 'daily_metrics' %}
SELECT
    variant,
    metric_date,
    COUNT(DISTINCT user_id) AS users,
    SUM(converted) AS conversions,
    AVG(converted) AS conversion_rate,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS avg_revenue
FROM `{{ dataset }}.ab_test_metrics`
WHERE test_id = '{{ test_id }}'
GROUP BY variant, metric_date
ORDER BY metric_date

{% elif query_type == 'segment_metrics' %}
SELECT
    a.{{ segment_dimension }} AS segment,
    a.variant,
    COUNT(DISTINCT m.user_id) AS users,
    SUM(m.converted) AS conversions,
    AVG(m.converted) AS conversion_rate,
    AVG(m.revenue) AS avg_revenue
FROM `{{ dataset }}.ab_test_metrics` m
JOIN `{{ dataset }}.ab_test_assignments` a
    ON m.user_id = a.user_id AND a.test_id = '{{ test_id }}'
WHERE m.test_id = '{{ test_id }}'
GROUP BY segment, a.variant

{% endif %}
