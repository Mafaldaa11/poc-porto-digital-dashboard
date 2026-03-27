import geopandas as gpd
import pydeck as pdk
import pandas as pd
from shapely.geometry import Point
from shapely.geometry import LineString
import numpy as np
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide") # Define o layout da página como "wide" para usar toda a largura disponível

count = st_autorefresh(interval=60000, limit=100, key="datarefresh")  # Atualiza a cada 60 segundos (60000 ms)

st.sidebar.header("Configurações do Mapa") # Adiciona um cabeçalho na barra lateral para as configurações do mapa
show_heatmap = st.sidebar.checkbox("Exibir Heatmap de Densidade 🔥", value=True)
show_wifi = st.sidebar.checkbox("Exibir Pontos de Wi-Fi 📶", value=True)
show_rotas = st.sidebar.checkbox("Exibir Rotas da STCP 🚌", value=True)

layers = [] # Lista para armazenar as camadas que serão exibidas no mapa, permitindo controle dinâmico com os checkboxes

@st.cache_data
def criar_heatmap():
    # 1. Carregar e Processar Dados de Residentes (Polígonos)
    gdf = gpd.read_file('file.geojson')
    gdf_filtrado = gdf[['N_INDIVIDUOS', 'geometry']]
    gdf_metros = gdf_filtrado.to_crs('EPSG:32629')

    # Cálculos de área e densidade
    gdf_metros['area_km2'] = gdf_metros['geometry'].area / 1e6
    gdf_metros['densidade'] = gdf_metros['N_INDIVIDUOS'] / gdf_metros['area_km2']

    # Usamos o centroide calculado na projeção métrica para precisão, convertido para 4326
    centroides_4326 = gdf_metros.geometry.centroid.to_crs(epsg=4326)
    gdf_metros['lon'] = centroides_4326.x
    gdf_metros['lat'] = centroides_4326.y

    # 3. Configuração Visual
    # Escala: Amarelo Claro -> Laranja -> Vermelho -> Vermelho Escuro
    COLOR_RANGE = [
        [255, 255, 178],
        [254, 204, 92],
        [253, 141, 60],
        [252, 78, 42],
        [227, 26, 28],
        [189, 0, 38]
    ]
    
    return pdk.Layer("HeatmapLayer",
        gdf_metros,
        get_position=["lon", "lat"],
        get_weight="densidade",
        radiusPixels=60,
        intensity=1,
        colorRange=COLOR_RANGE,
    )

@st.cache_data
def pontos_wifi():
    # 2. Carregar Dados de Wi-Fi (Pontos)
    df_wifi = pd.read_excel('Localização_Pontos_Wifi.xlsx')
    df_wifi = df_wifi.dropna(subset=['Latitude', 'Longitude'])
    geometry_wifi = [Point(xy) for xy in zip(df_wifi['Longitude'], df_wifi['Latitude'])]
    gdf_wifi = gpd.GeoDataFrame(df_wifi, geometry=geometry_wifi, crs='EPSG:4326')
    
    return pdk.Layer("ScatterplotLayer",
        gdf_wifi,
        get_position="geometry.coordinates",
        get_fill_color=[0, 0, 255, 200],
        get_radius=40,
        pickable=True,
    )

@st.cache_data
def rotas_stcp():
    # 3. Carregar dados das linhas STCP
    gdf_stcp = gpd.read_file('Dados_STCP.geojson')
    gdf_stcp = gdf_stcp.to_crs(epsg=4326)  # Certificar que está em WGS84 para o Pydeck

    gdf_stcp = gdf_stcp.explode(index_parts=False)  # Explode para lidar com múltiplas linhas em um único registro

    def desenhar_rotas(geom):
        if geom.geom_type == 'LineString': # Se for uma linha simples, extrai as coordenadas diretamente
            return [list(p[:2]) for p in geom.coords] # Extrai apenas as coordenadas (lon, lat) para cada ponto da linha
        return None # Para outros tipos de geometria, retorna None (ou poderia ser uma lista vazia) 
    
    gdf_stcp['path'] = gdf_stcp.geometry.apply(desenhar_rotas)

    #  Remove linhas que não tenham geometria válida (opcional, por segurança)
    gdf_stcp = gdf_stcp.dropna(subset=['path'])
    
    return pdk.Layer("PathLayer",
        gdf_stcp,
        get_path="path",
        get_color=[255, 0, 0],
        width_scale=10,
        width_min_pixels=2,
        pickable=True,
    )

layers = [] # Lista para armazenar as camadas que serão exibidas no mapa, permitindo controle dinâmico com os checkboxes    

if show_heatmap:
    layers.append(criar_heatmap())

if show_wifi:
    layers.append(pontos_wifi())

if show_rotas:
    layers.append(rotas_stcp())

# 5. Renderização
view_state = pdk.ViewState(latitude=41.15, longitude=-8.62, zoom=12, pitch=0, bearing=0)

r = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style=None,  # Usa o tema do Streamlit
    height=800,
    tooltip={}
)

st.pydeck_chart(r, use_container_width=True) # Exibe o mapa usando toda a largura disponível do contêiner do Streamlit