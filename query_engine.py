import duckdb
import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

def extract_sql(text):
    """Extract SQL code from LLM response using regex or fallback."""
    # Prefer code block format
    match = re.search(r"```sql\s+(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Otherwise return raw text
    return text.strip()

def ask_question(question, df):
    # Use GPT to generate SQL
    prompt = f"""
Generate a DuckDB SQL query to answer: '{question}'
Here is the table schema: {df.dtypes.to_dict()}
The table name is 'df'.
Only return the SQL, no explanation.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes valid DuckDB SQL queries."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_response = response.choices[0].message.content
    sql = extract_sql(raw_response)

    # Register DataFrame as DuckDB table
    con = duckdb.connect()
    con.register("df", df)

    # Run the SQL safely
    result = con.execute(sql).df()
    return sql, result
