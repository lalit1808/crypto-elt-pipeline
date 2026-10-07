import psycopg2
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "warehouse",
    "password": "warehouse",
    "dbname": "warehouse_db",
}

st.set_page_config(page_title="Crypto Analytics", layout="wide")


@st.cache_data(ttl=300)
def load_table(query):
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def forecast_prices(df, days_ahead=7):
    df = df.sort_values("price_date")
    x = np.arange(len(df))
    y = df["avg_price_eur"].values

    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)

    future_x = np.arange(len(df), len(df) + days_ahead)
    future_prices = trend(future_x)

    last_date = pd.to_datetime(df["price_date"].max())
    future_dates = [last_date + pd.Timedelta(days=i + 1) for i in range(days_ahead)]

    return pd.DataFrame({
        "price_date": future_dates,
        "avg_price_eur": future_prices,
    })


st.title("Crypto Analytics Dashboard")

coins_df = load_table("SELECT coin_id FROM staging_marts.dim_tracked_coins ORDER BY coin_id")
selected_coin = st.sidebar.selectbox("Select coin", coins_df["coin_id"])

tab1, tab2, tab3 = st.tabs(["Price Trend & Forecast", "Daily Top Movers", "Hourly Top Movers"])

with tab1:
    st.subheader(f"{selected_coin} — price history and 7-day forecast")

    full_history = load_table(f"""
        SELECT price_date, avg_price_eur
        FROM staging_marts.fact_price_history
        WHERE coin_id = '{selected_coin}'
        ORDER BY price_date
    """)

    if len(full_history) > 0:
        min_date = pd.to_datetime(full_history["price_date"]).min().date()
        max_date = pd.to_datetime(full_history["price_date"]).max().date()

        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            history = full_history[
                (pd.to_datetime(full_history["price_date"]).dt.date >= start_date) &
                (pd.to_datetime(full_history["price_date"]).dt.date <= end_date)
            ]
        else:
            history = full_history

        if len(history) >= 3:
            forecast = forecast_prices(history, days_ahead=7)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=history["price_date"], y=history["avg_price_eur"],
                mode="lines", name="Actual", line=dict(color="royalblue")
            ))
            fig.add_trace(go.Scatter(
                x=forecast["price_date"], y=forecast["avg_price_eur"],
                mode="lines", name="Forecast (linear trend)",
                line=dict(color="orange", dash="dash")
            ))
            fig.update_layout(xaxis_title="Date", yaxis_title="Avg Price (EUR)", height=500)
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "Forecast is a simple linear trend projection, not a trained model. "
                "Treat it as a rough directional indicator, not a prediction."
            )
        else:
            st.info("Not enough history in this range to forecast. Need at least 3 days of data.")
    else:
        st.info("No history available for this coin yet.")

with tab2:
    st.subheader("Daily Top Movers")

    available_dates = load_table("""
        SELECT DISTINCT price_date FROM staging_marts.mart_daily_top_movers
        ORDER BY price_date DESC
    """)

    selected_date = st.selectbox(
        "Select date",
        available_dates["price_date"],
        index=0,
    )

    daily_movers = load_table(f"""
        SELECT coin_id, price_date, open_price_eur, close_price_eur, pct_change, gainer_rank, loser_rank
        FROM staging_marts.mart_daily_top_movers
        WHERE price_date = '{selected_date}'
        ORDER BY pct_change DESC
    """)

    top_n = 10
    chart_data = pd.concat([
        daily_movers.head(top_n),
        daily_movers.tail(top_n)
    ]).drop_duplicates(subset="coin_id").sort_values("pct_change")

    colors = ["crimson" if v < 0 else "seagreen" for v in chart_data["pct_change"]]

    fig2 = go.Figure(go.Bar(
        x=chart_data["pct_change"],
        y=chart_data["coin_id"],
        orientation="h",
        marker_color=colors,
        text=chart_data["pct_change"].apply(lambda v: f"{v:+.2f}%"),
        textposition="outside",
    ))
    fig2.update_layout(
        title=f"Top gainers and losers — {selected_date}",
        xaxis_title="% Change",
        yaxis_title="",
        height=500,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(daily_movers, use_container_width=True)

with tab3:
    st.subheader("Hourly Top Movers (last hour vs previous)")

    hourly_movers = load_table("""
        SELECT coin_id, previous_price_eur, current_price_eur, pct_change, gainer_rank, loser_rank
        FROM staging_marts.mart_hourly_top_movers
        ORDER BY pct_change DESC
    """)

    top_n = 10
    chart_data_h = pd.concat([
        hourly_movers.head(top_n),
        hourly_movers.tail(top_n)
    ]).drop_duplicates(subset="coin_id").sort_values("pct_change")

    colors_h = ["crimson" if v < 0 else "seagreen" for v in chart_data_h["pct_change"]]

    fig3 = go.Figure(go.Bar(
        x=chart_data_h["pct_change"],
        y=chart_data_h["coin_id"],
        orientation="h",
        marker_color=colors_h,
        text=chart_data_h["pct_change"].apply(lambda v: f"{v:+.2f}%"),
        textposition="outside",
    ))
    fig3.update_layout(
        title="Top gainers and losers — last hour",
        xaxis_title="% Change",
        yaxis_title="",
        height=500,
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(hourly_movers, use_container_width=True)