import streamlit as st
import matplotlib.pyplot as plt
from utils import session_setup

st.title("Liste des produits")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

st.title("Produits les plus rentables")
prod = df_clients_filtered.groupby(['StockCode', 'Description']).agg({'Revenue': 'sum', 'Quantity': 'sum'}).sort_values(
    'Revenue', ascending=False).reset_index()
st.dataframe(prod.head(20))

st.subheader("Top 10 produits par CA")
fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(prod['Description'].head(10)[::-1], prod['Revenue'].head(10)[::-1], color='green')
ax.set_xlabel("CA (£)")
ax.set_title("Top 10 produits")
st.pyplot(fig)
