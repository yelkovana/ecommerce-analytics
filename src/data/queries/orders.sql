-- Orders & Revenue queries

{% if query_type == 'revenue_kpis' %}
SELECT
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.user_id) AS unique_customers,
    SUM(o.order_total) AS gmv,
    SUM(o.net_revenue) AS net_revenue,
    AVG(o.order_total) AS aov,
    SUM(oi.quantity) AS units_sold
FROM `{{ dataset }}.orders` o
LEFT JOIN `{{ dataset }}.order_items` oi ON o.order_id = oi.order_id
WHERE DATE(o.order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'

{% elif query_type == 'daily_revenue' %}
SELECT
    DATE(order_date) AS date,
    COUNT(DISTINCT order_id) AS orders,
    SUM(order_total) AS revenue,
    AVG(order_total) AS aov
FROM `{{ dataset }}.orders`
WHERE DATE(order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY date
ORDER BY date

{% elif query_type == 'cohort' %}
WITH user_cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC(MIN(DATE(order_date)), {{ cohort_period | default('MONTH') }}) AS cohort
    FROM `{{ dataset }}.orders`
    GROUP BY user_id
)
SELECT
    uc.cohort AS cohort_month,
    DATE_TRUNC(DATE(o.order_date), {{ cohort_period | default('MONTH') }}) AS order_month,
    COUNT(DISTINCT o.user_id) AS users,
    SUM(o.order_total) AS revenue,
    COUNT(DISTINCT o.order_id) AS orders
FROM `{{ dataset }}.orders` o
JOIN user_cohorts uc ON o.user_id = uc.user_id
WHERE DATE(o.order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month

{% elif query_type == 'product_performance' %}
SELECT
    oi.product_id,
    oi.category_l1,
    oi.category_l2,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    SUM(oi.quantity) AS units_sold,
    COUNT(DISTINCT o.order_id) AS order_count
FROM `{{ dataset }}.order_items` oi
JOIN `{{ dataset }}.orders` o ON oi.order_id = o.order_id
WHERE DATE(o.order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY oi.product_id, oi.category_l1, oi.category_l2
ORDER BY revenue DESC
LIMIT {{ limit | default(100) }}

{% elif query_type == 'category_performance' %}
SELECT
    oi.category_l1,
    oi.category_l2,
    {% if include_l3 %}oi.category_l3,{% endif %}
    SUM(oi.quantity * oi.unit_price) AS revenue,
    SUM(oi.quantity) AS units_sold,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.user_id) AS unique_customers
FROM `{{ dataset }}.order_items` oi
JOIN `{{ dataset }}.orders` o ON oi.order_id = o.order_id
WHERE DATE(o.order_date) BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY oi.category_l1, oi.category_l2{% if include_l3 %}, oi.category_l3{% endif %}
ORDER BY revenue DESC

{% endif %}
