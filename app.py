import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt

# ----- PAGE CONFIG -----
st.set_page_config(page_title="HVAC Dashboard", layout="wide")
page = st.sidebar.radio("Go to", ["Executive Summary", "Occupancy", "Setpoint & Comfort Monitoring","Forecasting Model and Evaluation"])

# ----- LOAD DATA -----
df = pd.read_csv("hvac_updated.csv", parse_dates=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_name()

# Create 'month_year' column for trend analysis
df["month_year"] = df["timestamp"].dt.to_period("M").astype(str)

# ----- EXECUTIVE SUMMARY PAGE -----
if page == "Executive Summary":
    st.title("⚡ Executive Summary – Energy & Carbon Efficiency KPIs")

    # ----- KPI CALCULATIONS -----
    total_actual_energy = df["actual_cooling_load_kWh"].sum()
    total_baseline_energy = df["baseline_cooling_load"].sum()
    total_predicted_energy = df["predicted_cooling_load_kWh"].sum()
    total_energy_saved = total_baseline_energy - df["optimized_cooling_load_kWh"].sum()

    average_occupancy_pct = df["occupancy_pct"].mean()
    comfort_compliance_pct = ((df["adjusted_setpoint"] >= 22) & (df["adjusted_setpoint"] <= 25)).mean() * 100
    peak_occupancy_count = df["occupancy_count"].max()

    # ----- KPI DISPLAY -----
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("⚡ Total Actual Energy (kWh)", f"{total_actual_energy:,.0f}")
    with col2: st.metric("🏛️ Total Baseline Energy (kWh)", f"{total_baseline_energy:,.0f}")
    with col3: st.metric("📊 Total Predicted Energy (kWh)", f"{total_predicted_energy:,.0f}")
    with col4: st.metric("✅ Total Energy Saved (kWh)", f"{total_energy_saved:,.0f}")

    st.markdown("")
    col5, col6, col7 = st.columns(3)
    with col5: st.metric("👥 Avg. Occupancy (%)", f"{average_occupancy_pct:.1f}%")
    with col6: st.metric("🌡️ Comfort Compliance (%)", f"{comfort_compliance_pct:.1f}%")
    with col7: st.metric("🚶‍♂️ Peak Occupancy Count", f"{peak_occupancy_count}")

    st.markdown("## 📈 Energy Performance")

    # ----- LINE CHART: Monthly Cooling Load Trend -----
    st.markdown("### 📅 Monthly Cooling Load Trend")
    monthly_trend_df = df.groupby("month_year")["actual_cooling_load_kWh"].sum().reset_index()

    fig = px.line(
    monthly_trend_df,
    x="month_year",  # ✅ Use the correct column name
    y="actual_cooling_load_kWh",
    markers=True,
    labels={"month_year": "Month", "actual_cooling_load_kWh": "Cooling Load (kWh)"},
    title="Cooling Load Trend Over Months"
)

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Cooling Load (kWh)",
        font=dict(color="#262730"),
        
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----- BAR CHART: Zone-wise Cooling Load -----
    st.markdown("### 🗂️ Energy Consumption by Zone")
    zone_energy_df = df.groupby("zone_id")["actual_cooling_load_kWh"].sum().reset_index()
    zone_energy_df = zone_energy_df.sort_values(by="actual_cooling_load_kWh", ascending=False)

    fig = px.bar(
        zone_energy_df,
        x="zone_id",
        y="actual_cooling_load_kWh",
        color="actual_cooling_load_kWh",
        color_continuous_scale="Blues",
        labels={"zone_id": "Zone", "actual_cooling_load_kWh": "Cooling Load (kWh)"},
        title="Zone-wise Cooling Load Consumption"
    )
    fig.update_layout(
        xaxis_title="Zone",
        yaxis_title="Total Cooling Load (kWh)",
        coloraxis_colorbar=dict(title="kWh"),
        font=dict(color="#262730"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----- DONUT CHART: Cooling Load by Zone Function -----
    st.markdown("### 🍩 Cooling Load Distribution by Zone Function")
    function_df = df.groupby("zone_function")["actual_cooling_load_kWh"].sum().reset_index()

    fig = px.pie(
        function_df,
        values="actual_cooling_load_kWh",
        names="zone_function",
        title="Cooling Load Share by Functional Area",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(
        showlegend=True,
        font=dict(color="#262730"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Occupancy":
    st.title("📍 Occupancy Analytics")

    # ----- 1. HEATMAP -----
    st.markdown("### 🕒 Occupancy Heatmap by Hour & Day")

    pivot_df = df.pivot_table(index='day_of_week', columns='hour', values='occupancy_pct', aggfunc='mean')
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_df = pivot_df.reindex(days_order)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(pivot_df, cmap="YlGnBu", linewidths=0.5, annot=True, fmt=".0f", ax=ax)
    plt.xlabel("Hour of Day")
    plt.ylabel("Day of Week")
    st.pyplot(fig)

    # ----- 3. SCATTER: OCCUPANCY VS COOLING -----
    st.markdown("### 🔁 Correlation: Occupancy % vs Cooling Demand")

    scatter = alt.Chart(df).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X('occupancy_pct', title='Occupancy %'),
        y=alt.Y('actual_cooling_load_kWh', title='Cooling Load (kWh)'),
        color=alt.Color('occupancy_pct',
                        scale=alt.Scale(scheme='orangered'),
                        legend=alt.Legend(title='Occupancy %')),
        tooltip=['occupancy_pct', 'actual_cooling_load_kWh']
    ).properties(
        width='container',
        height=350
    ).interactive()

    st.altair_chart(scatter, use_container_width=True)


elif page == "Setpoint & Comfort Monitoring":
    st.title("🌡️ Zone-wise Setpoint Monitoring")

    # Time Interval selector
    interval = st.selectbox("Choose Time Interval", ["Hourly", "Daily"])

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create time group
    if interval == "Hourly":
        df['time_group'] = df['timestamp'].dt.floor('H')
    else:
        df['time_group'] = df['timestamp'].dt.floor('D')

    # Group by zone and time
    df_grouped = df.groupby(['zone_id', 'time_group']).agg({
        'standard_setpoint': 'mean',
        'adjusted_setpoint': 'mean'
    }).reset_index()

    # Melt for Altair
    df_melted = df_grouped.melt(
        id_vars=['zone_id', 'time_group'],
        value_vars=['standard_setpoint', 'adjusted_setpoint'],
        var_name='Setpoint Type',
        value_name='Value'
    )

    # Line Chart
    st.markdown(f"### 📊 {interval} Setpoint Trends by Zone")

    chart = alt.Chart(df_melted).mark_line(point=True).encode(
        x=alt.X('time_group:T', title='Time'),
        y=alt.Y('Value:Q', title='Setpoint'),
        color='zone_id:N',
        strokeDash='Setpoint Type:N',
        tooltip=['zone_id:N', 'time_group:T', 'Setpoint Type:N', 'Value:Q']
    ).properties(
        width='container',
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Optional Data Preview
    st.markdown("### 📄 Aggregated Data Preview")
    st.dataframe(df_grouped.head())




    # ----- 2. BOXPLOT: ZONE COMFORT DISTRIBUTION -----
    st.markdown("### 📦 Zone-Wise Adjusted Setpoint Distribution")

    box_plot = alt.Chart(df).mark_boxplot(extent='min-max').encode(
        x=alt.X('zone_type:N', title='Zone Type'),
        y=alt.Y('adjusted_setpoint:Q', title='Adjusted Setpoint (°C)'),
        color=alt.Color('zone_type:N', legend=None),
        tooltip=['zone_type:N', 'adjusted_setpoint:Q']
    ).properties(
        width='container',
        height=350
    )

    st.altair_chart(box_plot, use_container_width=True)
    
    # ----- FORECASTING MODEL AND EVALUATION PAGE -----
elif page == "Forecasting Model and Evaluation":
    st.title("📉 Forecasting Model Evaluation")

    # Ensure required columns exist
    if "actual_cooling_load_kWh" in df.columns and "predicted_cooling_load_kWh" in df.columns:

        # Calculate absolute error
        df["prediction_error"] = abs(df["actual_cooling_load_kWh"] - df["predicted_cooling_load_kWh"])

        # Optionally extract month for grouping (if 'timestamp' column exists)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["Month"] = df["timestamp"].dt.strftime('%b-%Y')

        # 1. 📦 ERROR DISTRIBUTION BOXPLOT
        st.markdown("### 📦 Distribution of Absolute Errors")
        if "Month" in df.columns:
            box_fig = px.box(
                df,
                x="Month",
                y="prediction_error",
                title="Distribution of Absolute Errors by Month",
                labels={
                    "Month": "Month",
                    "prediction_error": "Absolute Error (kWh)"
                },
                color_discrete_sequence=["#636EFA"]
            )
        else:
            box_fig = px.box(
                df,
                y="prediction_error",
                title="Distribution of Absolute Errors",
                labels={
                    "prediction_error": "Absolute Error (kWh)"
                },
                color_discrete_sequence=["#636EFA"]
            )
        box_fig.update_layout(
            xaxis_title="Month" if "Month" in df.columns else "",
            yaxis_title="Absolute Error (kWh)",
            font=dict(color="#262730"),
            
        )
        st.plotly_chart(box_fig, use_container_width=True)

        # 2. 🔍 SCATTER PLOT: Predicted vs Actual
        st.markdown("### 🔍 Predicted vs Actual Cooling Load")
        scatter_fig = px.scatter(
            df,
            x="predicted_cooling_load_kWh",
            y="actual_cooling_load_kWh",
            title="Predicted vs Actual Cooling Load",
            labels={
                "predicted_cooling_load_kWh": "Predicted Cooling Load (kWh)",
                "actual_cooling_load_kWh": "Actual Cooling Load (kWh)"
            },
            opacity=0.6,
            trendline="ols",
            color_discrete_sequence=["#EF553B"]
        )
        scatter_fig.update_layout(
            font=dict(color="#262730"),
            
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    else:
        st.warning("The dataset must contain 'actual_cooling_load_kWh' and 'predicted_cooling_load_kWh' columns.")
