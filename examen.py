import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import numpy as np

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

# Carrera más común del año seleccionado
st.subheader("🏆 Most Commonly Chosen Major in Selected Year")
departments = ['Engineering Enrolled', 'Business Enrolled', 'Arts Enrolled', 'Science Enrolled']
most_common_major = filtered_df[departments].sum().idxmax().replace(" Enrolled", "")
st.write(f"The most commonly chosen major in {selected_year} was {most_common_major}.")

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

# Nueva sección: Tasa de Conversión
tab5, tab6 = st.tabs(["📊 Conversion Rate", "📈 Correlation Analysis"])

with tab5:
    st.subheader("🔄 Application-to-Enrollment Conversion Rate")
    df['Conversion Rate (%)'] = (df['Enrolled'] / df['Applications']) * 100
    fig = px.line(df, x='Year', y='Conversion Rate (%)', markers=True, title="Conversion Rate Over the Years")
    st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("🔗 Correlation Heatmap")
    corr_matrix = df[['Applications', 'Admitted', 'Enrolled', 'Retention Rate (%)', 'Student Satisfaction (%)']].corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
    st.pyplot(fig)

st.markdown("---")

st.subheader("📢 Key Insights")
"""
### Insights from Data Analysis on Student Retention and Satisfaction

#### 1. Retention Rate Trends Over Time
- The retention rate has shown an overall upward trend from 2015 to 2024, with some fluctuations.
- A significant drop occurred around 2020, likely due to the impact of the COVID-19 pandemic.
- From 2020 onwards, there has been a steady recovery, reaching its highest point in 2024.
- **Recommendation:** Breaking down retention rates by department could help identify which areas contribute most to retention gains or declines.

#### 2. Enrollment Breakdown by Department
- Engineering consistently has the highest enrollment numbers throughout the years.
- Business follows as the second-largest department, showing continuous growth.
- Arts and Sciences maintain relatively stable but lower enrollment figures, with slight fluctuations.
- **Interesting pattern:** While Engineering and Business grow, Sciences show slight declines in certain periods.
- **Recommendation:** If increasing enrollment in specific departments is a goal, investigating factors driving growth in Engineering and Business could help apply similar strategies to underperforming areas.

#### 3. Student Satisfaction Trends
- Student satisfaction has been on a steady rise from 2015 to 2024, with minor fluctuations.
- A decline around 2020 is noticeable, likely due to pandemic-related disruptions in education.
- Post-pandemic recovery suggests the university has implemented improvements in the student experience.
- In 2024, satisfaction reaches its highest level in the dataset.

#### 4. Correlation Analysis
- **Applications, admissions, and enrollments are highly correlated (~1.00),** indicating a strong interdependence between these processes.
- **Student satisfaction is strongly correlated with applications and admissions (~0.99 and 0.98, respectively).** This suggests that improving the student experience attracts more applicants.
- **Retention rate has a lower correlation with other variables (0.85-0.88),** implying that while related, additional factors influence whether students stay enrolled.

### General Conclusions
- **Enhancing student satisfaction can boost retention and attract more applicants.**
- **Retention is more volatile than satisfaction,** meaning external factors may impact student persistence.
- **Analyzing retention fluctuations by department and year could help identify critical factors affecting student persistence.**
- If retention drops in certain years, investigating external events or policy changes could lead to proactive strategies for improvement.
"""

