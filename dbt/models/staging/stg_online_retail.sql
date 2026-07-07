with source as (
    select * from {{ source('bronze', 'online_retail') }}
),

-- Same invoice/product/date/qty/price can legitimately repeat (e.g. two identical
-- lines on one order); this discriminates them so the surrogate key stays unique.
numbered as (
    select
        *,
        row_number() over (
            partition by InvoiceNo, StockCode, InvoiceDate, Quantity, UnitPrice
            order by InvoiceNo
        ) as _line_occurrence
    from source
),

renamed as (
    select
        sha2(concat_ws('-', InvoiceNo, StockCode, InvoiceDate, Quantity, UnitPrice, _line_occurrence), 256) as invoice_line_id,
        InvoiceNo as invoice_id,
        InvoiceNo like 'C%' as is_cancellation,
        StockCode as product_code,
        Description as product_description,
        Quantity as quantity,
        UnitPrice as unit_price,
        Quantity * UnitPrice as line_amount,
        InvoiceDate as invoice_at,
        CustomerID as customer_id,
        Country as country
    from numbered
)

select * from renamed
