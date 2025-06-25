import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import date

# Load your cleaned data
df = pd.read_csv("../data/cleaned/tasas_sistema_bancario_full.csv")

# Convert 'fecha' column to datetime
if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
    df['fecha'] = pd.to_datetime(df['fecha'])

st.title("Tasas Sistema Bancario")

# KPI: Show the most recent 'compra' value in a blueish box
if not df.empty:
    most_recent_row = df.sort_values('fecha').iloc[-1]
    st.markdown(
        f"""
        <div style='background-color: #e3f0ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #1a4a7a; margin: 0;'>Compra más reciente</h3>
            <p style='font-size: 2em; color: #1a4a7a; margin: 0;'><b>{most_recent_row['compra']:.4f}</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Add filter: type bank name
bank_query = st.text_input("Nombre del banco (puedes escribir parte del nombre):", "Banesco")

if bank_query:
    filtered_df = df[df['banco'].str.contains(bank_query, case=False, na=False)]
else:
    filtered_df = df.copy()


# Convert to date for Streamlit slider
min_date = filtered_df['fecha'].min().date()
max_date = filtered_df['fecha'].max().date()

# Set default initial date to January 1, 2024 if in range
initial_date = date(2024, 1, 1)
if initial_date < min_date:
    initial_date = min_date
if initial_date > max_date:
    initial_date = min_date  # fallback if all data is before 2024

selected_range = st.slider(
    "Rango de Fecha",
    min_value=min_date,
    max_value=max_date,
    value=(initial_date, max_date),
    format="YYYY-MM-DD"
)

filtered_df = filtered_df[
    (filtered_df['fecha'].dt.date >= selected_range[0]) &
    (filtered_df['fecha'].dt.date <= selected_range[1])
]

# Show a line chart for 'compra' amount
if not filtered_df.empty:
    chart_df = filtered_df.copy()
    chart_df = chart_df.sort_values('fecha')
    st.subheader('Evolución de la tasa de compra')
    st.line_chart(
        data=chart_df.set_index('fecha')['compra'],
        use_container_width=True
    )

# Format 'compra' to 4 decimals and 'fecha' to only date (no time)
display_df = filtered_df.copy()
display_df['compra'] = display_df['compra'].map(lambda x: f"{x:.4f}")
if 'venta' in display_df.columns:
    display_df['venta'] = display_df['venta'].map(lambda x: f"{x:.4f}")
display_df['fecha'] = display_df['fecha'].dt.strftime('%Y-%m-%d')   

st.dataframe(display_df)

# Add download button for Excel
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()

st.download_button(
    label="Descargar tabla como Excel",
    data=processed_data,
    file_name="tasas_filtradas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
