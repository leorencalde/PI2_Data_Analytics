import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# Función para cargar y combinar los datos desde la base de datos SQLite
def load_data():
    conn = sqlite3.connect('1. Datasets/siniestros_viales.db')
    
    hechos_df = pd.read_sql_query('SELECT * FROM hechos', conn)
    victimas_df = pd.read_sql_query('SELECT * FROM victimas', conn)
    
    conn.close()
    
    # Eliminar las columnas ALTURA, CRUCE y DIRECCION_NORMALIZADA
    hechos_df.drop(columns=['Altura', 'Cruce', 'Dirección Normalizada'], inplace=True)
    
    # Combinar los datos de hechos y víctimas
    combined_df = pd.merge(hechos_df, victimas_df, left_on='ID', right_on='ID_hecho', how='left')
    
    # Convertir las columnas 'POS_X' y 'POS_Y' a valores numéricos, manejando errores
    combined_df['pos x'] = pd.to_numeric(combined_df['pos x'], errors='coerce')
    combined_df['pos y'] = pd.to_numeric(combined_df['pos y'], errors='coerce')
    
    # Limpiar la columna 'EDAD' convirtiéndola a valores numéricos, manejando errores
    combined_df['EDAD'] = pd.to_numeric(combined_df['EDAD'], errors='coerce')
    
    # Eliminar los valores nulos del dataframe combinado
    combined_df.dropna(inplace=True)

    # Renombrar las columnas 'POS_Y' y 'POS_X' a 'latitude' y 'longitude'
    combined_df.rename(columns={'pos y': 'latitude', 'pos x': 'longitude'}, inplace=True)
    
    return combined_df

# Cargar los datos
data = load_data()

# Crear el dashboard con Streamlit
st.title('Dashboard de Siniestros Viales en CABA')

# Filtros de selección
st.sidebar.header('Filtros')
anio = st.sidebar.selectbox('Año', sorted(data['AAAA_x'].unique()))
mes = st.sidebar.selectbox('Mes', sorted(data['MM_x'].unique()))

# Filtrar los datos según los filtros seleccionados
filtered_data = data[(data['AAAA_x'] == anio) & (data['MM_x'] == mes)]

# KPI 1: Tasa de homicidios en siniestros viales
poblacion_total = 3075646  # Población de CABA
num_homicidios = filtered_data['ID_hecho'].nunique()
tasa_homicidios = (num_homicidios / poblacion_total) * 100000
st.metric('Tasa de Homicidios en Siniestros Viales', f'{tasa_homicidios:.2f} por 100,000 habitantes')

# KPI 2: Cantidad de accidentes mortales de motociclistas
num_accidentes_motos = filtered_data[filtered_data['VICTIMA_y'] == 'MOTO']['ID_hecho'].nunique()
st.metric('Accidentes Mortales de Motociclistas', num_accidentes_motos)

# Visualización de los datos
st.subheader('Mapa de Siniestros Viales')
st.map(filtered_data[['latitude', 'longitude']])

st.subheader('Distribución de Homicidios por Edad y Sexo')
fig, ax = plt.subplots()
filtered_data['EDAD'].hist(ax=ax, bins=30)
ax.set_xlabel('Edad')
ax.set_ylabel('Cantidad')
st.pyplot(fig)

st.subheader('Homicidios por Tipo de Participante')
fig, ax = plt.subplots()
filtered_data['VICTIMA_y'].value_counts().plot(kind='bar', ax=ax)
ax.set_xlabel('Tipo de Participante')
ax.set_ylabel('Cantidad')
st.pyplot(fig)
