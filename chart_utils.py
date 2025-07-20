import plotly.express as px
import pandas as pd

def show_chart(df):
    if df.shape[1] < 2:
        return None

    x, y = df.columns[:2]

    # Only proceed if y looks numeric
    if not pd.api.types.is_numeric_dtype(df[y]):
        return None

    # Choose chart type based on x column
    if pd.api.types.is_datetime64_any_dtype(df[x]) or pd.api.types.is_string_dtype(df[x]):
        fig = px.bar(df, x=x, y=y)
    else:
        fig = px.scatter(df, x=x, y=y)

    fig.update_layout(title="Auto-generated Chart", xaxis_title=x, yaxis_title=y)
    return fig
