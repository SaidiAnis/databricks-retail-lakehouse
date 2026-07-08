-- One row per product_code. Description can vary slightly across rows for the
-- same code (manual data entry); max_by picks the one from the latest invoice.
select
    product_code,
    max_by(product_description, invoice_at) as product_description
from {{ ref('stg_online_retail') }}
group by product_code
