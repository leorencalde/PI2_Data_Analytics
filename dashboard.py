import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import altair as alt

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
        
    # Renombrar las columnas 'POS_Y' y 'POS_X' a 'latitude' y 'longitude'
    combined_df.rename(columns={'pos y': 'latitude', 'pos x': 'longitude'}, inplace=True)

    # Eliminar los valores nulos del dataframe combinado
    combined_df.dropna(subset=['latitude', 'longitude'], inplace=True)
    
    return combined_df

# Cargar los datos
data = load_data()

# Crear el dashboard con Streamlit
st.title('Análisis de Datos de Siniestros Viales en la Ciudad Autónoma de Buenos Aires')

# Filtros de selección
st.sidebar.header('Filtros')
anio = st.sidebar.selectbox('Año', ['Todos'] + sorted(data['AAAA_x'].unique().tolist()))

# Filtrar los datos según los filtros seleccionados
if anio != 'Todos':
    filtered_data = data[data['AAAA_x'] == anio]
else:
    filtered_data = data

# Calcular el número total de siniestros viales
total_siniestros_viales = data['N_VICTIMAS'].sum()

# Mostrar el número total de siniestros viales
st.subheader('Número Total de Siniestros Viales (2016-2021)')
st.metric('Total de Siniestros Viales', total_siniestros_viales)

# Agregar gráfico interactivo del total de siniestros viales
st.subheader('Total de Siniestros Viales (2016-2021)')
total_siniestros = data.groupby(['AAAA_x']).size().reset_index(name='counts')
chart = alt.Chart(total_siniestros).mark_line(point=True).encode(
    x='AAAA_x:O',
    y='counts:Q',
    tooltip=['AAAA_x', 'counts']
).interactive()

st.altair_chart(chart, use_container_width=True)

# Gráfico de incidencia de accidentes por meses
st.subheader('Incidencia de Accidentes por Mes')
monthly_accidents = filtered_data.groupby(['AAAA_x', 'MM_x']).size().reset_index(name='counts')
monthly_chart = alt.Chart(monthly_accidents).mark_bar().encode(
    x=alt.X('MM_x:O', title='Mes'),
    y=alt.Y('counts:Q', title='Total de Siniestros'),
    color='AAAA_x:N',
    tooltip=['AAAA_x', 'MM_x', 'counts']
).properties(
    title='Incidencia de Accidentes por Mes'
).interactive()

st.altair_chart(monthly_chart, use_container_width=True)

# Visualización de Mapa Siniestros Viales
st.subheader('Mapa de Siniestros Viales')
if 'latitude' in filtered_data.columns and 'longitude' in filtered_data.columns:
    st.map(filtered_data[['latitude', 'longitude']])

# Gráfico de comunas versus cantidad de siniestros
st.subheader('Comunas vs Cantidad de Siniestros')
comuna_accidents = filtered_data['COMUNA'].value_counts().reset_index()
comuna_accidents.columns = ['Comuna', 'Número de Accidentes']
comuna_chart = alt.Chart(comuna_accidents).mark_bar().encode(
    x=alt.X('Comuna:O', sort='-y'),
    y='Número de Accidentes:Q',
    tooltip=['Comuna', 'Número de Accidentes']
).properties(
    title='Cantidad de Siniestros por Comuna'
).interactive()

st.altair_chart(comuna_chart, use_container_width=True)

# KPIs propuestos para el proyecto
st.subheader('Propuesta de KPIs')

# KPI 1: Tasa de homicidios en siniestros viales
st.subheader('1. Tasa de Homicidios en Siniestros Viales')
poblacion_total = 3075646  # Población de CABA
num_homicidios = filtered_data['ID_hecho'].nunique()
tasa_homicidios = (num_homicidios / poblacion_total) * 100000
st.metric('Tasa de Homicidios en Siniestros Viales', f'{tasa_homicidios:.2f} por 100,000 habitantes')

# KPI 1: Gráfico de la tasa de homicidios en siniestros viales por año
homicidios_anual = data.groupby('AAAA_x')['ID_hecho'].nunique().reset_index()
homicidios_anual['tasa_homicidios'] = (homicidios_anual['ID_hecho'] / poblacion_total) * 100000
homicidios_chart = alt.Chart(homicidios_anual).mark_line(point=True).encode(
    x='AAAA_x:O',
    y='tasa_homicidios:Q',
    tooltip=['AAAA_x', 'tasa_homicidios']
).properties(
    title='Tasa de Homicidios en Siniestros Viales por Año'
).interactive()

st.altair_chart(homicidios_chart, use_container_width=True)

# KPI 1: Tasa de homicidios en siniestros viales
st.subheader('Objetivo: Reducir esta tasa en un 10% en los próximos seis meses')

# KPI 2: Cantidad de accidentes mortales de motociclistas
st.subheader('2. Cantidad de accidentes mortales de motociclistas')
num_accidentes_motos = filtered_data[filtered_data['VICTIMA_y'] == 'MOTO']['ID_hecho'].nunique()
st.metric('Accidentes Mortales de Motociclistas', num_accidentes_motos)

# KPI 2: Cantidad de accidentes mortales de motociclistas
accidentes_motos_anual = data[data['VICTIMA_y'] == 'MOTO'].groupby('AAAA_x')['ID_hecho'].nunique().reset_index()
accidentes_motos_chart = alt.Chart(accidentes_motos_anual).mark_bar().encode(
    x='AAAA_x:O',
    y='ID_hecho:Q',
    tooltip=['AAAA_x', 'ID_hecho']
).properties(
    title='Accidentes Mortales de Motociclistas por Año'
).interactive()

st.altair_chart(accidentes_motos_chart, use_container_width=True)

# KPI 2: Cantidad de accidentes mortales de motociclistas
st.subheader('Objetivo: Reducir estos accidentes en un 7% en el próximo año')

# Resultados Clave y Propuestas de Medidas
st.header('Resultados Clave y Propuestas de Medidas')

# Medida 1
st.subheader('1. Mejorar la señalización vial y la iluminación en áreas de alta incidencia')
st.markdown("""
Estudios realizados en Londres han demostrado que mejorar la señalización y la iluminación puede reducir los accidentes en hasta un 30% (fuente: Transport for London).
""")

# Medida 2
st.subheader('2. Incrementar los controles de alcoholemia y velocidad en las zonas críticas')
st.markdown("""
En Nueva York, la implementación de controles estrictos de velocidad y alcoholemia ha llevado a una reducción del 25% en los accidentes fatales (fuente: NYC Department of Transportation).
""")

# Medida 3
st.subheader('3. Realizar campañas educativas dirigidas a jóvenes y motociclistas para promover comportamientos de conducción más seguros')
st.markdown("""
En Suecia, las campañas educativas dirigidas a jóvenes conductores han resultado en una disminución significativa de accidentes en este grupo etario (fuente: Swedish Transport Administration).
""")
