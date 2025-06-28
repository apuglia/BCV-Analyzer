import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import date
import subprocess
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Layout: Title and Refresh Button
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Tasas Sistema Bancario")
with col2:
    if st.button("Actualizar datos"):
        with st.spinner("Actualizando datos..."):
            # Use correct paths for the scripts
            get_tasas_script = os.path.join(script_dir, "get_tasas.py")
            clean_tasas_script = os.path.join(script_dir, "clean_tasas.py")
            subprocess.run(["python", get_tasas_script])
            subprocess.run(["python", clean_tasas_script])
        st.success("Datos actualizados. Recargando...")
        st.rerun()  # Reload the app to show new data

# Load your cleaned data (after possible update)
# Fix path to work both locally and when deployed
csv_path = os.path.join(script_dir, "..", "data", "cleaned", "tasas_sistema_bancario_full.csv")

if not os.path.exists(csv_path):
    st.error(f"File not found: {csv_path}. Please run the data preparation scripts first.")
    st.stop()

df = pd.read_csv(csv_path)

# Show the date of the last data point
if not df.empty and 'fecha' in df.columns:
    last_date = pd.to_datetime(df['fecha']).max().strftime('%Y-%m-%d')
    st.info(f"Última fecha de datos: {last_date}")

# Convert 'fecha' column to datetime
if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
    df['fecha'] = pd.to_datetime(df['fecha'])

# KPI: Show the average 'compra' value across all banks for the most recent date
if not df.empty:
    # Get the most recent date
    most_recent_date = df['fecha'].max()
    
    # Filter data for the most recent date and calculate average compra
    most_recent_data = df[df['fecha'] == most_recent_date]
    avg_compra = most_recent_data['compra'].mean()
    
    # Count how many banks reported data for that date
    num_banks = len(most_recent_data)
    
    st.markdown(
        f"""
        <div style='background-color: #e3f0ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #1a4a7a; margin: 0;'>Promedio de compra más reciente</h3>
            <p style='font-size: 2em; color: #1a4a7a; margin: 0;'><b>{avg_compra:.4f}</b></p>
            <p style='color: #1a4a7a; margin: 5px 0 0 0; font-size: 0.9em;'>Basado en {num_banks} bancos ({most_recent_date.strftime('%Y-%m-%d')})</p>
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

# Show percentage change chart
if not filtered_df.empty:
    chart_df = filtered_df.copy()
    chart_df = chart_df.sort_values('fecha')
    
    # Calculate daily percentage change (day-to-day)
    chart_df['pct_change_daily'] = chart_df['compra'].pct_change() * 100
    
    # Calculate statistics for daily changes
    daily_changes = chart_df['pct_change_daily'].dropna()
    
    if not daily_changes.empty:
        # Display metrics for daily changes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cambio Promedio Diario", f"{daily_changes.mean():.2f}%")
        with col2:
            st.metric("Cambio Máximo Diario", f"{daily_changes.max():.2f}%")
        with col3:
            st.metric("Cambio Mínimo Diario", f"{daily_changes.min():.2f}%")
        
        # Show daily percentage change chart
        st.subheader('Cambio porcentual diario')
        st.line_chart(
            data=chart_df.set_index('fecha')['pct_change_daily'],
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
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # Ensure the writer is properly closed
    processed_data = output.getvalue()

st.download_button(
    label="Descargar tabla como Excel",
    data=processed_data,
    file_name="tasas_filtradas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
