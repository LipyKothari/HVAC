import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt

# ----- PAGE CONFIG -----
st.set_page_config(page_title="HVAC Dashboard", layout="wide")
page = st.sidebar.radio("Go to", ["Executive Summary", "Occupancy", "Setpoint & Comfort Monitoring","Forecasting Model and Evaluation", "Operational Overview"])

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
    total_energy_saved = df["baseline_cooling_load"].sum() - df["optimized_cooling_load_kWh"].sum()
    average_occupancy_pct = df["occupancy_pct"].mean()
    comfort_compliance_pct = ((df["adjusted_setpoint"] >= 22) & (df["adjusted_setpoint"] <= 25)).mean() * 100

    # ----- KPI DISPLAY -----
    col1, col2 = st.columns(2)
    with col1:
        st.metric("⚡ Total Actual Energy (kWh)", f"{total_actual_energy:,.0f}")
    with col2:
        st.metric("✅ Total Energy Saved (kWh)", f"{total_energy_saved:,.0f}")

    st.markdown("")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("👥 Avg. Occupancy (%)", f"{average_occupancy_pct:.1f}%")
    with col4:
        st.metric("🌡️ Comfort Compliance (%)", f"{comfort_compliance_pct:.1f}%")

    st.markdown("## Energy Performance")

    # ----- BAR CHART: Zone-wise Cooling Load -----
    st.markdown("### Energy Consumption by Zone")
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
    st.markdown("### Cooling Load Distribution by Zone Function")
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
    
    # ----- LINE CHART: Monthly Cooling Load Trend -----
    st.markdown("### Monthly Cooling Load Trend")
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

# ----- SETPOINT & COMFORT MONITORING PAGE -----
elif page == "Setpoint & Comfort Monitoring":
    st.title("🌡️ Zone-wise Setpoint Monitoring")

    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Select interval
    interval = st.selectbox("Choose Time Interval", ["Hourly", "Daily"])

    # Create time_group column
    if interval == "Hourly":
        df['time_group'] = df['timestamp'].dt.floor('H')
    else:
        df['time_group'] = df['timestamp'].dt.floor('D')

    # Optional: zone filter to avoid clutter
    zones = df['zone_id'].unique().tolist()
    selected_zone = st.selectbox("Select Zone", sorted(zones))

    df_zone = df[df['zone_id'] == selected_zone]

    # Group and aggregate
    df_grouped = df_zone.groupby(['time_group']).agg({
        'standard_setpoint': 'mean',
        'adjusted_setpoint': 'mean'
    }).reset_index()

    # Plot using Plotly
    fig = px.line(
        df_grouped,
        x="time_group",
        y=["standard_setpoint", "adjusted_setpoint"],
        labels={"value": "Setpoint (°C)", "time_group": "Time"},
        title=f"{selected_zone} - Setpoint Monitoring ({interval})"
    )
    fig.update_traces(mode='lines+markers')
    fig.update_layout(
        legend_title_text="Setpoint Type",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

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

    group_col = st.selectbox("Group setpoints by:", ["zone_type", "zone_function"])

    df_filtered = df.dropna(subset=[group_col, "adjusted_setpoint"])

    fig_box = px.box(
        df_filtered,
        x=group_col,
        y="adjusted_setpoint",
        color=group_col,
        points="outliers",
        title=f"Distribution of Adjusted Setpoints by {group_col.replace('_', ' ').title()}",
    )

    fig_box.update_layout(
        xaxis_title=group_col.replace('_', ' ').title(),
        yaxis_title="Adjusted Setpoint (°C)",
        font=dict(color="#262730"),
        showlegend=False
    )

    st.plotly_chart(fig_box, use_container_width=True)
    
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
        
# ----- OPERATIONAL OVERVIEW PAGE -----
elif page == "Operational Overview":
    st.title("⚙️ Operational Overview")

    # 1. Daily Aggregated Trends
    st.subheader("📊 Daily Aggregated Occupancy Trends")

    # Ensure 'timestamp' is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create 'date' column
    df['date'] = df['timestamp'].dt.date

    # Group by date
    daily_df = df.groupby('date').agg({
        'rolling_avg_occupancy_3h': 'mean',
        'rolling_max_occupancy_6h': 'max'
    }).reset_index()

    # Reshape for single plot
    daily_avg = daily_df[['date', 'rolling_avg_occupancy_3h']].rename(
        columns={'rolling_avg_occupancy_3h': 'Occupancy', 'date': 'Date'})
    daily_avg['Metric'] = '3h Rolling Avg Occupancy'

    daily_max = daily_df[['date', 'rolling_max_occupancy_6h']].rename(
        columns={'rolling_max_occupancy_6h': 'Occupancy', 'date': 'Date'})
    daily_max['Metric'] = '6h Rolling Max Occupancy'

    combined_df = pd.concat([daily_avg, daily_max])

    # Plot using Plotly with custom colors
    fig = px.line(
        combined_df,
        x='Date',
        y='Occupancy',
        color='Metric',
        title='📈 Daily Rolling Avg (3h) and Max (6h) Occupancy',
        labels={'Date': 'Date', 'Occupancy': 'Occupancy (%)'},
        markers=True,
        color_discrete_map={
            '3h Rolling Avg Occupancy': 'blue',
            '6h Rolling Max Occupancy': 'red'
        }
    )

    fig.update_layout(
        xaxis=dict(tickangle=45),
        legend_title_text='',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    # 2. Zoning Mode Summary
    st.subheader("🏢 Zoning Mode Distribution")

    if "zoning_mode" in df.columns:
        zoning_counts = df["zoning_mode"].value_counts().reset_index()
        zoning_counts.columns = ["Zoning Mode", "Count"]

        fig_zone = px.bar(
            zoning_counts,
            x="Zoning Mode",
            y="Count",
            color="Zoning Mode",
            title="Zoning Mode Usage Frequency",
            text_auto=True
        )
        fig_zone.update_layout(showlegend=False)
        st.plotly_chart(fig_zone, use_container_width=True)
    else:
        st.warning("Zoning mode data not found.")

