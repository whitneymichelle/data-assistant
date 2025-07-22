import duckdb
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

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
            ]
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
