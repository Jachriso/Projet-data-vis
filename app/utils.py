import streamlit as st
import pandas as pd

'''
@st.cache_data
def load_data():
    file_path = "../data/online_retail_II.xlsx"
    df_sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    df = pd.concat(df_sheets.values(), ignore_index=True)

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Revenue'] = df['Quantity'] * df['Price']
    df['Annulation'] = df['Invoice'].astype(str).str.startswith('C')
    df.loc[df['Annulation'], 'Revenue'] *= -1
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['Day'] = df['InvoiceDate'].dt.date
    df['Month'] = df['InvoiceDate'].dt.to_period('M')

    df_clients = df[~df['Annulation']].copy()
    df_clients['is_return'] = df_clients['Quantity'] < 0
    df_clients['is_damage'] = (df_clients['Quantity'] < 0) & (df_clients['Price'] == 0)

    return df, df_clients
'''

@st.cache_data
def load_data():
    # Lecture des CSV compressés
    df = pd.read_csv("data/processed/retail_clean_full.csv.gz", compression="gzip")
    df_clients = pd.read_csv("data/processed/retail_clean_clients.csv.gz", compression="gzip")

    # S'assurer que les dates sont bien au format datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df_clients['InvoiceDate'] = pd.to_datetime(df_clients['InvoiceDate'])
    df['Revenue'] = df['Quantity'] * df['Price']
    df['Annulation'] = df['Invoice'].astype(str).str.startswith('C')
    df.loc[df['Annulation'], 'Revenue'] *= -1
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['Day'] = df['InvoiceDate'].dt.date
    df['Month'] = df['InvoiceDate'].dt.to_period('M')

    df_clients = df[~df['Annulation']].copy()
    df_clients['is_return'] = df_clients['Quantity'] < 0
    df_clients['is_damage'] = (df_clients['Quantity'] < 0) & (df_clients['Price'] == 0)

    return df, df_clients

