import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# Cargar datos
@st.cache_data
def load_data():
    file_path = 'university_student_dashboard_data.csv'  # Ajustar la ruta según sea necesario
    return pd.read_csv(file_path)

df = load_data()

# Configuración de la página
st.set_page_config(page_title="University Dashboard", layout="wide")

# Título del dashboard
st.title("📊 University Student Dashboard")
st.markdown("---")

# Sidebar para filtros
years = df['Year'].unique()
selected_year = st.sidebar.selectbox("Select Year", years)
filtered_df = df[df['Year'] == selected_year]

# Métricas clave
st.subheader("📌 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Applications", filtered_df["Applications"].sum())
col2.metric("Total Admitted", filtered_df["Admitted"].sum())
col3.metric("Total Enrolled", filtered_df["Enrolled"].sum())


# Aplicación más común del año seleccionado
st.subheader("🏆 Most Common Application in Selected Year")
most_common_application = filtered_df.groupby('Applications').size().idxmax()
st.write(f"The most common application count in {selected_year} was {most_common_application} applications.")

st.markdown("---")

# Gráfica de tendencias de retención
st.subheader("📈 Retention Rate Trends Over Time")
fig = px.line(df, x='Year', y='Retention Rate (%)', markers=True, title="Retention Rate Over the Years")
st.plotly_chart(fig, use_container_width=True)

# Gráfica de satisfacción estudiantil
tab1, tab2 = st.tabs(["📊 Satisfaction Over Time", "📊 Enrollment by Department"])

with tab1:
    st.subheader("😊 Student Satisfaction Over the Years")
    fig = px.line(df, x='Year', y='Student Satisfaction (%)', markers=True, color_discrete_sequence=['green'])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🏫 Enrollment Breakdown by Department")
    department_totals = df.groupby('Year')[['Engineering Enrolled', 'Business Enrolled', 'Arts Enrolled', 'Science Enrolled']].sum()
    fig = px.bar(department_totals, x=department_totals.index, y=department_totals.columns,
                 barmode='group', title="Enrollment Trends by Department")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Comparación Spring vs. Fall
tab3, tab4 = st.tabs(["🌸 Spring vs Fall Trends", "📌 Retention & Satisfaction Comparison"])

with tab3:
    st.subheader("📅 Spring vs. Fall Term Trends")
    spring_fall_comparison = df.groupby(['Year', 'Term'])[['Retention Rate (%)', 'Student Satisfaction (%)']].mean().reset_index()
    fig = px.line(spring_fall_comparison, x='Year', y=['Retention Rate (%)', 'Student Satisfaction (%)'], color='Term', markers=True)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("📊 Retention Rate & Satisfaction Levels")
    fig = px.line(df, x='Year', y=['Retention Rate (%)', 'Student Satisfaction (%)'], markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("📢 Key Insights")
st.write("- The retention rate has shown a steady trend over the years with some fluctuations.")
st.write("- Student satisfaction levels have varied but follow a general upward trend.")
st.write("- Enrollment in different departments exhibits interesting shifts, potentially influenced by job market trends.")
st.write("- Spring and Fall term trends highlight key differences in student engagement and retention.")

st.success("✅ This dashboard provides valuable insights for university decision-makers!")
