import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
@st.cache_data
def load_data():
    file_path = 'university_student_dashboard_data.csv'  # Ajustar la ruta según sea necesario
    return pd.read_csv(file_path)

df = load_data()

# Título del dashboard
st.title("University Student Dashboard")

# Mostrar datos
st.subheader("Vista previa de los datos")
st.write(df.head())

# 1. Total applications, admissions, and enrollments per year & term
st.subheader("Total Applications, Admissions, and Enrollments per Year & Term")
metrics_per_term_year = df.groupby(['Year', 'Term'])[['Applications', 'Admitted', 'Enrolled']].sum()
st.write(metrics_per_term_year)

# 2. Retention rate trends over time
st.subheader("Retention Rate Trends Over Time")
fig, ax = plt.subplots()
ax.plot(df['Year'], df['Retention Rate (%)'], marker='o', linestyle='-', label='Retention Rate')
ax.set_xlabel('Year')
ax.set_ylabel('Retention Rate (%)')
ax.set_title('Retention Rate Trends Over Time')
ax.legend()
st.pyplot(fig)

# 3. Student satisfaction over years
st.subheader("Student Satisfaction Over the Years")
fig, ax = plt.subplots()
ax.plot(df['Year'], df['Student Satisfaction (%)'], marker='s', linestyle='-', color='g', label='Student Satisfaction')
ax.set_xlabel('Year')
ax.set_ylabel('Student Satisfaction (%)')
ax.set_title('Student Satisfaction Over the Years')
ax.legend()
st.pyplot(fig)

# 4. Enrollment breakdown by department
st.subheader("Total Enrollment by Department")
departments = ['Engineering Enrolled', 'Business Enrolled', 'Arts Enrolled', 'Science Enrolled']
department_totals = df[departments].sum()
fig, ax = plt.subplots()
department_totals.plot(kind='bar', color=['b', 'r', 'g', 'purple'], ax=ax)
ax.set_title('Total Enrollment by Department')
ax.set_xlabel('Department')
ax.set_ylabel('Total Enrolled')
st.pyplot(fig)

# 5. Spring vs. Fall term trends
st.subheader("Comparison Between Spring vs. Fall Term Trends")
spring_fall_comparison = df.groupby(['Year', 'Term'])[['Retention Rate (%)', 'Student Satisfaction (%)']].mean().reset_index()
spring_fall_pivot = spring_fall_comparison.pivot(index='Year', columns='Term', values=['Retention Rate (%)', 'Student Satisfaction (%)'])
st.write(spring_fall_pivot)

# 6. Compare trends between departments, retention rates, and satisfaction levels
st.subheader("Enrollment Trends by Department Over Time")
fig, ax = plt.subplots()
for department in departments:
    ax.plot(df.groupby('Year')[department].sum(), marker='o', linestyle='-', label=department)
ax.set_xlabel('Year')
ax.set_ylabel('Enrollment')
ax.set_title('Enrollment Trends by Department Over Time')
ax.legend()
st.pyplot(fig)

st.subheader("Retention Rate & Student Satisfaction Over Time")
fig, ax = plt.subplots()
ax.plot(df.groupby('Year')['Retention Rate (%)'].mean(), marker='o', linestyle='-', label='Retention Rate', color='b')
ax.plot(df.groupby('Year')['Student Satisfaction (%)'].mean(), marker='s', linestyle='-', label='Student Satisfaction', color='g')
ax.set_xlabel('Year')
ax.set_ylabel('Percentage')
ax.set_title('Retention Rate & Student Satisfaction Over Time')
ax.legend()
st.pyplot(fig)

