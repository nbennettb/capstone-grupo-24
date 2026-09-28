import pandas as pd
import geopandas as gpd
import pyogrio
import matplotlib.pyplot as plt

# # Extraer el polígono de la RM ya identificado
admin = gpd.read_file("chile.gpkg", layer="gis_osm_adminareas_a_free", engine="pyogrio")
rm_poly = admin[admin['name'] == 'Región Metropolitana de Santiago']

# # Usar ese polígono como máscara para leer SOLO lo que cae dentro de la RM
roads_rm = gpd.read_file(
    "chile.gpkg",
    layer="gis_osm_roads_free",
    mask=rm_poly,
    engine="pyogrio"
)
# print("roads_rm:", roads_rm.shape)
# print(roads_rm['fclass'].value_counts())  # tipos de vía (motorway, primary, residential, etc.)

transport_rm = gpd.read_file(
    "chile.gpkg",
    layer="gis_osm_transport_free",
    mask=rm_poly,
    engine="pyogrio"
)
# print("\ntransport_rm:", transport_rm.shape)
# print(transport_rm['fclass'].value_counts())  # esto te dirá si trae paraderos, terminales, etc.


# 1. Cruzar tus depots contra bus_station reales de OSM
bus_stations = transport_rm[transport_rm['fclass'] == 'bus_station']
# print(bus_stations[['name', 'geometry']])

depots = pd.read_csv("depots.csv")
depots_gdf = gpd.GeoDataFrame(
    depots,
    geometry=gpd.points_from_xy(depots['lon'], depots['lat']),
    crs="EPSG:4326"
)


# 2. Filtrar vías relevantes
vias_relevantes = ['motorway','motorway_link','trunk','trunk_link','primary','primary_link',
                    'secondary','secondary_link','tertiary','tertiary_link','busway']
roads_filtradas = roads_rm[roads_rm['fclass'].isin(vias_relevantes)]
# print(f"\nVías filtradas: {len(roads_filtradas)} de {len(roads_rm)}")




# # --- Visualización ---

# # Reproyectar todo a metros (UTM 19S) para que el mapa se vea proporcionado
# rm_poly_m = rm_poly.to_crs("EPSG:32719")
# roads_m = roads_filtradas.to_crs("EPSG:32719")
# bus_stops_m = transport_rm[transport_rm['fclass'] == 'bus_stop'].to_crs("EPSG:32719")
# depots_m = depots_gdf.to_crs("EPSG:32719")

# fig, ax = plt.subplots(figsize=(10, 12))

# # Fondo: polígono de la RM
# rm_poly_m.plot(ax=ax, color="#f0f0f0", edgecolor="black", linewidth=1)

# # Red vial filtrada
# roads_m.plot(ax=ax, color="gray", linewidth=0.4, alpha=0.6)

# # Paraderos de bus
# bus_stops_m.plot(ax=ax, color="steelblue", markersize=1, alpha=0.4)

# # Electroterminales destacados
# depots_m.plot(ax=ax, color="red", markersize=120, marker="^", edgecolor="black", zorder=5)
# for idx, row in depots_m.iterrows():
#     ax.annotate(row['nombre'], xy=(row.geometry.x, row.geometry.y),
#                 xytext=(5, 5), textcoords="offset points", fontsize=9, fontweight="bold")

# ax.set_title("Red vial, paraderos y electroterminales — Región Metropolitana", fontsize=13)
# ax.set_axis_off()
# plt.tight_layout()
# plt.savefig("mapa_electroterminales_rm.png", dpi=200, bbox_inches="tight")
# plt.show()

