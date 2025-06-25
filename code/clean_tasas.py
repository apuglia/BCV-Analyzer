import pandas as pd
import os
import unicodedata
import re

def clean_banco_column(banco):
    # Remove accents
    banco = unicodedata.normalize('NFKD', banco).encode('ASCII', 'ignore').decode('utf-8')
    # Remove special characters (keep alphanumerics and spaces)
    banco = re.sub(r'[^\w\s]', '', banco)
    return banco

def clean_tasas(input_path, output_path):
    # Read the HTML table(s)
    tables = pd.read_html(input_path)
    df = tables[0]  # Use the first table found

    # Clean 'Fecha del Indicador' column to YYYY-MM-DD
    df['Fecha del Indicador'] = pd.to_datetime(
        df['Fecha del Indicador'], errors='coerce', dayfirst=True
    ).dt.strftime('%Y-%m-%d')

    # Clean 'Banco' column: remove accents and special characters
    df['Banco'] = df['Banco'].astype(str).apply(clean_banco_column)

    # Rename 'Fecha del Indicador' to 'fecha'
    df = df.rename(columns={'Fecha del Indicador': 'fecha'})

    # Convert all column names to lowercase and strip spaces
    df.columns = [col.strip().lower() for col in df.columns]

    # Scale 'compra' and 'venta' columns to correct units BEFORE dropping NaNs
    if 'compra' in df.columns:
        df['compra'] = df['compra'] / 10000
    if 'venta' in df.columns:
        df['venta'] = df['venta'] / 10000

    # Now drop NaNs
    df_cleaned = df.dropna()

    # Save the cleaned data to CSV
    df_cleaned.to_csv(output_path, index=False)

if __name__ == "__main__":
    raw_path = os.path.join("..", "data", "raw", "tasas_sistema_bancario_full.xls")
    cleaned_path = os.path.join("..", "data", "cleaned", "tasas_sistema_bancario_full.csv")
    clean_tasas(raw_path, cleaned_path) 