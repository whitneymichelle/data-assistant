## "Chat with Your Data Assistant": Explore and Visualize Data with Natural Language ##


### Overview ###
**Chat with Your Data Assistant** is a Streamlit app that lets you explore and ask questions in natural language. Whether a data expert or business stakeholder, you can upload a CSV and automatically generate SQL, visualizations, and dbt tests - no coding required.

### Demo
[![Watch the demo](https://cdn.loom.com/sessions/thumbnails/0ef838c9c9b94e869239e9d28abefc4c-a58a8f121cf6172a.jpg)](https://www.loom.com/share/0ef838c9c9b94e869239e9d28abefc4c)

### Features ###
- Upload a CSV and preview the data
- Get automatic data insights - trends within a business context
- Ask questions in natural language
- View SQL used to generate responses
- Get charts (bar, line) based on query results
- Generate dbt test YAML from your schema

### Try Asking Your Assistant ###
- What is the average rating over time?
- What is the sales by category?
- What are the top 5 popular categories?
- What dbt tests might be helpful?

### How It Works ##
1. User uploads a CSV
2. App parses the file and shows a preview
3. A background AI agent analyzes the dataset and infers useful metadata
4. User asks questions — app determines intent:
   - If SQL → generates SQL and runs it on DuckDB
   - If dbt test → generates dbt YAML from schema
5. Outputs result, visualization, and chat history

### How to Run Locally ##
1. `git clone data-assistant`
2. `cd data-assistant`
3. `poetry install`
4. `poetry run streamlit run app.py`

> 💡 Requires an OpenAI API key

### Known Limitations ##
- May return irrelevant results for vague or overly complex questions
- Does not support multi-file joins
- Visualizations are auto-chosen based on result shape

## License
This project is licensed under the MIT License.