import duckdb
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from examples_for_ai import AGG_KEYWORDS, YAML_SAMPLE
import pandas as pd

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

def define_intent(text):
    if "dbt test" in text.lower():
        return "dbt_test"
    else:
        return "sql_query"

def extract_sql(text):
    """Extract SQL code from LLM response using regex or fallback."""
    # Prefer code block format
    match = re.search(r"```sql\s+(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Otherwise return raw text
    return text.strip()

def extract_yaml(raw_response: str) -> str:
    """
    Extracts YAML content from a code block in the LLM response.
    Looks for triple backtick blocks with or without 'yaml' language hint.
    """
    # Try to find a code block with optional language (e.g. ```yaml or ```yml)
    match = re.search(r"```(?:yaml|yml)?\s*(.*?)```", raw_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: just return the whole response if no code block found
    return raw_response.strip()

def mentions_aggregation(question):
    question = question.lower()
    return any(keyword in question for keyword in AGG_KEYWORDS)

def requested_column_is_numeric(question, df):
    for col in df.columns:
        if col.lower() in question.lower():
            return pd.api.types.is_numeric_dtype(df[col])
    return True #default to True

def ask_question(question, df):
    # Get schema info
    schema = df.dtypes.to_dict()

    # Only sample unique values from columns with few distinct values
    value_samples = {
        col: df[col].dropna().unique()[:5].tolist()
        for col in df.columns
        if df[col].nunique() <= 15  # Adjust threshold as needed
    }

    intent = define_intent(question)

    # Use GPT to generate SQL
    if intent == "dbt_test":
        prompt = f"""
        Generate a dbt tests to answer: '{question}'
        Here is the table schema: {schema}
        The table name is 'df'.
        Here is an example of a dbt schema YAML file and you should follow this structure: {YAML_SAMPLE}

        Your task is to generate valid dbt schema YAML (version 2) for a given DataFrame.
        Always follow this structure exactly:

        - Use `version: 2` at the top.
        - Use `models` → `name`, `description`, and `columns`.
        - Each column should include a `description` and `tests` block.
        - Tests should include common ones like `not_null`, `unique`, or `accepted_values`.
        - For numeric columns, include `dbt_expectations.expect_column_values_to_be_between` if applicable.
        - For foreign keys, use the `relationships` test.
        - Add **YAML comments above each test** explaining what the test is doing and why it's useful.

        Only return the YAML inside a Markdown code block (```yaml). Do not explain anything outside of the YAML.
        """

    else:
        prompt = f"""
        Generate a DuckDB SQL query to answer: '{question}'
        Here is the table schema: {schema}
        The table name is 'df'.
        Here are sample values from some columns (to avoid incorrect assumptions):{value_samples}
        Only use column values that exist in the samples provided.
        Only return the SQL, no explanation.
        In your SQL outputs, structure the results for readability: first the category or label (e.g., year, region, product), then the numerical values (e.g., avg_price, count)
        "Only apply numeric aggregations (e.g., AVG, SUM) to columns with numeric data types (int64, float64)."
        """

    if intent == "dbt_test":
        system_prompt = (
        "You are a senior analytics engineer. Generate meaningful custom dbt tests in YAML format.\n"
        "Only output valid dbt schema YAML (version 2). Include columns and test types.\n"
        "Add YAML comments explaining each test. Do not include anything outside the code block."
    )
    else:
        system_prompt = (
        "You are a helpful assistant that writes valid DuckDB SQL queries.\n"
        "You write clean DuckDB SQL. You prefer grouping/category columns first and numeric aggregates second."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
            ],
        temperature=0

        )

    raw_response = response.choices[0].message.content

    if intent == "dbt_test":
        # Extract YAML from response
        yml = extract_yaml(raw_response)
        return yml, None
    else:
        sql = extract_sql(raw_response)
        # Register DataFrame as DuckDB table
        con = duckdb.connect()
        con.register("df", df)
        # Run the SQL safely
        result = con.execute(sql).df()
        return sql, result

def find_insights(df):
    # Get schema info
    schema = df.dtypes.to_dict()

    # Only sample unique values from columns with few distinct values
    value_samples = {
        col: df[col].dropna().unique()[:5].tolist()
        for col in df.columns
        if df[col].nunique() <= 15  # Adjust threshold as needed
    }

    prompt = f"""
    Here is the table schema: {schema}
    Here are sample values from some columns (to avoid incorrect assumptions):{value_samples}
    The table name is 'df'.
    Generate three insights in bulleted format, focusing insights on trends, anomalies, or patterns that could inform business decisions.
    The insights can be any combination of trends, anomalies, or patterns.
    The bullet points headings should be descriptive, taking into acount the business context.
    Focus on readability and clarity and give an explanation of why it might be important.
    The format should be:
        - Insight 1
        - Insight 2
        - Insight 3
    """

    system_prompt = f"""
    "You are a data analyst that generates meaningful insights for business decisions.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
            ]
        )

    raw_response = response.choices[0].message.content

    return raw_response

def suggest_models(df):
    # Get schema info
    schema = df.dtypes.to_dict()

    # Only sample unique values from columns with few distinct values
    value_samples = {
        col: df[col].dropna().unique()[:5].tolist()
        for col in df.columns
        if df[col].nunique() <= 15  # Adjust threshold as needed
    }

    prompt = f"""
    Here is the table schema: {schema}
    Here are sample values from some columns (to avoid incorrect assumptions):{value_samples}
    The table name is 'df'.
    A surrogate key is a synthetic, unique identifier for a row — usually an auto-incrementing integer — that isn't derived from the business data itself.
    If a fact table makes sense, create a DuckDB SQL query to create it. Indicate the unique key or the surrogate key as the unique key. The unique key should be a single column and the first column.
    Give an explanation of the fact table
    If a dimension table makes sense, create a DuckDB SQL query to create it. Indicate the unique key. The unique key should be a single column and the first column.
    If a dimension table does not make sense to be a table, explain why.
    Write the fact table and dimensional table in DuckDB SQL, no DDL. For example 'select col_1, cols_2 from df'
    """

    system_prompt = f"""
    "You are an analytics engineer. Give suggestions on data models in the dimensional modeling framework."
    "When modeling data, identify surrogate keys by checking for numeric, high-cardinality, auto-increment-style columns that are not natural identifiers."
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
            ]
        )

    raw_response = response.choices[0].message.content

    return raw_response



