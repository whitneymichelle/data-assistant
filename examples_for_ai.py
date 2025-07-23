AGG_KEYWORDS = [
    "average", "avg", "mean",
    "sum", "total",
    "minimum", "min",
    "maximum", "max",
    "median", "mode",
    "percent", "percentage", "proportion",
    "aggregate", "aggregated",
    "grouped by", "group by",
    "histogram"
]

YAML_SAMPLE = """

version: 2

models:
  - name: orders
    description: Table containing ecommerce order data
    columns:
      - name: order_id
        description: Unique identifier for each order
        tests:
          - unique
          - not_null

      - name: customer_id
        description: Foreign key to the customers table
        tests:
          - not_null
          - relationships:
              to: ref('customers')
              field: customer_id

      - name: order_date
        description: Date when the order was placed
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_of_type:
              column_type: date

      - name: total_amount
        description: Total amount of the order in USD
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              strictly: true

      - name: status
        description: Order status (e.g., pending, shipped, delivered)
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'shipped', 'delivered', 'cancelled']

"""