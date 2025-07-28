import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt

# ----- PAGE CONFIG -----
st.set_page_config(page_title="HVAC Dashboard", layout="wide")
page = st.sidebar.radio("Go to", ["Executive Summary", "Occupancy", "Setpoint & Comfort Monitoring"])



# ----- LOAD DATA -----
df = pd.read_csv("hvac_updated.csv", parse_dates=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_name()

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

# ----- SETPOINT & COMFORT MONITORING PAGE -----
elif page == "Setpoint & Comfort Monitoring":
    st.title("🌡️ Setpoint & Comfort Monitoring")

    # ----- 1. LINE CHART: STANDARD VS ADJUSTED SETPOINT -----
    st.markdown("### 🔁 Standard vs Adjusted Setpoint Over Time")

    # Fold the two setpoint columns into one for Altair line chart
    line_chart = alt.Chart(df).transform_fold(
        ['standard_setpoint', 'adjusted_setpoint'],
        as_=['Setpoint_Type', 'Setpoint_Value']
    ).mark_line(point=True).encode(
        x=alt.X('timestamp:T', title='Timestamp'),
        y=alt.Y('Setpoint_Value:Q', title='Setpoint (°C)'),
        color=alt.Color('Setpoint_Type:N', title='Setpoint Type'),
        tooltip=['timestamp:T', 'Setpoint_Type:N', 'Setpoint_Value:Q']
    ).properties(
        width='container',
        height=350
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

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
