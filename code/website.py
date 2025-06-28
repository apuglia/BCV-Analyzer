import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import date
import subprocess
import os
import json

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
            get_bcv_script = os.path.join(script_dir, "get_bcv_official_rate.py")
            
            subprocess.run(["python", get_tasas_script])
            subprocess.run(["python", clean_tasas_script])
            subprocess.run(["python", get_bcv_script])
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


# Path to the rates file
bcv_rates_path = os.path.join(script_dir, "..", "data", "cleaned", "bcv_official_rates.json")

if os.path.exists(bcv_rates_path):
    with open(bcv_rates_path, "r", encoding="utf-8") as f:
        bcv_rates_data = json.load(f)
    value_date = bcv_rates_data.get("fecha_valor", "")
    rates = bcv_rates_data.get("rates", [])

    st.markdown(
        "<h3 style='color:#1a4a7a;'>Tasas Oficiales BCV</h3>",
        unsafe_allow_html=True
    )
    # Display as columns, USD first, with blueish background
    rates_sorted = sorted(rates, key=lambda r: 0 if r['code'] == 'USD' else 1)
    cols = st.columns(len(rates_sorted))
    for i, rate in enumerate(rates_sorted):
        value = rate['value'] / 100000000
        with cols[i]:
            st.markdown(
                f"""
                <div style='background-color: #e3f0ff; border-radius: 12px; padding: 12px 0 8px 0; text-align: center; margin-bottom: 8px;'>
                    <span style='font-size:1.1em; color:#1a4a7a; font-weight:600;'>{rate['symbol']} {rate['code']}</span><br>
                    <span style='font-size:1.0em; color:#222; font-weight:400;'>{value:,.2f}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.info("No se encontraron tasas oficiales BCV.")

st.markdown("<hr style='margin: 2em 0;'>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='color:#1a4a7a;'>Tasas USD en Bancos Venezolanos</h3>",
    unsafe_allow_html=True
)


# Add filter: type bank name
bank_query = st.text_input("Nombre del banco (puedes escribir parte del nombre):", "Banesco")

if bank_query:
    filtered_df = df[df['banco'].str.contains(bank_query, case=False, na=False)]
else:
    filtered_df = df.copy()


# After filtering filtered_df, add this KPI for latest compra
if not filtered_df.empty:
    latest_row = filtered_df.sort_values('fecha').iloc[-1]
    st.markdown(
        f"""
        <div style='background-color: #e3f0ff; padding: 16px; border-radius: 10px; margin-bottom: 18px; text-align: center;'>
            <span style='color: #1a4a7a; font-size: 1.1em; font-weight: 600;'>Compra más reciente (banco seleccionado)</span><br>
            <span style='font-size: 2em; color: #1a4a7a; font-weight: 700;'>{latest_row['compra']:.2f}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

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
    format="MMM D, YYYY"
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

st.markdown(
    "<style>.element-container .stMetric { min-width: 120px; }</style>",
    unsafe_allow_html=True
)


