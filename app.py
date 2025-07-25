import streamlit as st
import pandas as pd
from query_engine import ask_question, define_intent, find_insights, mentions_aggregation, requested_column_is_numeric
from chart_utils import show_chart
from preprocess_utils import coerce_dates

st.title("Chat with Your Data Assistant")

uploaded_file = st.file_uploader("Upload a CSV", type=["csv"])

if "messages" not in st.session_state:
    st.session_state.messages = []

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = coerce_dates(df)
    st.write("Preview your data:", df.head())
    st.markdown("I'm generating some initial insights for your data...")
    insights = find_insights(df)
    st.markdown(insights)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask a question about your data...(Try something like 'What is the average sales by category?' or 'What are some dbt tests I can run on this data?')")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        try:
            if define_intent(question) == "sql_query":

                if mentions_aggregation(question) and not requested_column_is_numeric(question, df):
                    st.warning("Warning: You may be trying to aggregate a non-numeric column.")

                sql, result = ask_question(question, df)
                chart = show_chart(result)
                response_content = (
                    "Here's the SQL I used:\n"
                    "```sql\n"
                    f"{sql}\n"
                    "```\n"
                    "And the result:"
                )

                st.session_state.messages.append({"role": "assistant", "content": response_content})

                with st.chat_message("assistant"):
                    st.markdown(response_content)
                    st.dataframe(result)
                    if chart:
                        st.plotly_chart(chart)

            else:
                yml = ask_question(question, df)[0]
                response_content = (
                    "Here's the YAML of dbt tests I created:\n"
                    "```yaml\n"
                    f"{yml}\n"
                    "```\n"
                )

                with st.chat_message("assistant"):
                    st.markdown(response_content)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.error(error_msg)