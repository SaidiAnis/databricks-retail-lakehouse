-- One row per known customer_id. Guest checkouts (null customer_id) have no
-- customer profile, so they are excluded here (they still exist in fct_sales).
select
    customer_id,
    max_by(country, invoice_at) as country,
    min(invoice_at) as first_order_at,
    max(invoice_at) as last_order_at
from {{ ref('stg_online_retail') }}
where customer_id is not null
group by customer_id
