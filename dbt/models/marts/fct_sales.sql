select
    invoice_line_id,
    invoice_id,
    invoice_at,
    date(invoice_at) as date_day,
    customer_id,
    product_code,
    quantity,
    unit_price,
    line_amount,
    is_cancellation
from {{ ref('stg_online_retail') }}
