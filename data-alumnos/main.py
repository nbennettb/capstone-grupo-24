import pandas as pd
df = pd.read_csv("charging_activities.csv", sep=None, engine="python")

# print(df.shape)
# print(df.head(10))
# print(df.dtypes)

# print(df.groupby("depot_id")["capacity"].nunique())   # ¿cada depot tiene un único valor de capacity en las 24 horas?
# print(df.groupby("depot_id")["capacity"].first())      # ese valor único, por depot
# print(df["charge_id"].str.split("_").str[1].astype(int).describe())  # confirma que start_hour va de 0 a 23

trips = pd.read_csv("gtfs/trips.txt")
routes = pd.read_csv("gtfs/routes.txt")
calendar = pd.read_csv("gtfs/calendar.txt")

# print("trips:", trips.shape)
# print(trips.head())
# print()
# print("routes:", routes.shape)
# print(routes.head())
# print()
# print("calendar:", calendar.shape)
# print(calendar.head())

# print(calendar)  # las 6 filas completas
# print()
# print(trips.columns.tolist())
# print(routes.columns.tolist())
# print()
# print(trips["service_id"].value_counts())
# print()
# # Explorar si existe alguna pista de "eléctrico" en routes
# print(routes.head(10).to_string())


stop_times = pd.read_csv("gtfs/stop_times.txt")
# print("stop_times:", stop_times.shape)
# print(stop_times.head())
# print(stop_times.dtypes)
# print()

shape_dist = pd.read_csv("shape_distances.csv")
# print("shape_distances:", shape_dist.shape)
# print(shape_dist.head())


# 1. Revisar cuántos registros tienen hora >= 24 (cruce de medianoche)
mask_24h = stop_times['arrival_time'].str.split(':').str[0].astype(int) >= 24
# print("Registros con hora >= 24:", mask_24h.sum(), "de", len(stop_times))

# 2. Convertir hora a minutos totales (manejando el >24h correctamente, NO usar to_datetime)
def time_to_min(t):
    h, m, s = map(int, t.split(':'))
    return h*60 + m + s/60

stop_times['t_min'] = stop_times['arrival_time'].apply(time_to_min)

# 3. Duración por viaje
trip_times = stop_times.groupby('trip_id')['t_min'].agg(start_min='min', end_min='max')
trip_times['duration_min'] = trip_times['end_min'] - trip_times['start_min']
# print(trip_times['duration_min'].describe())
# print("Duraciones sospechosas (<=0 min):", (trip_times['duration_min'] <= 0).sum())
# print(trip_times.sort_values('duration_min', ascending=False).head(5))


# 1. Confirmar la hipótesis: ¿cuántos trips (de los 26.137) parten en start_min=0?
pct_zero_start = (trip_times['start_min'] == 0).mean() * 100
# print(f"% de trips con start_min = 0: {pct_zero_start:.1f}%")

# 2. Revisar frequencies.txt — probablemente aquí está la hora real de partida
freq = pd.read_csv("gtfs/frequencies.txt")
# print("frequencies:", freq.shape)
# print(freq.head())
# print(freq.dtypes)

# 3. Investigar los viajes sospechosamente cortos (<=3 min)
cortos = trip_times[trip_times['duration_min'] <= 3]
# print(f"\nViajes con duración <= 3 min: {len(cortos)}")
# print(cortos.head(10))



# # 1. ¿Cuántos de los 26.137 trips tienen entrada en frequencies?
# trips_con_freq = trips['trip_id'].isin(freq['trip_id'])
# print(f"Trips con frecuencia definida: {trips_con_freq.sum()} de {len(trips)} ({trips_con_freq.mean()*100:.1f}%)")

# # 2. Expandir a número real de salidas por patrón (para dimensionar demanda real)
# freq['duracion_ventana_seg'] = (pd.to_datetime(freq['end_time']) - pd.to_datetime(freq['start_time'])).dt.total_seconds()
# freq['num_salidas'] = freq['duracion_ventana_seg'] / freq['headway_secs']
# print(f"\nTotal de salidas reales (expandiendo por headway): {freq['num_salidas'].sum():.0f}")
# print(freq['num_salidas'].describe())

# # 3. Investigar la segunda familia de trip_id (patrón "DX_...")
# import re
# patron_normal = trips['trip_id'].str.match(r'^\d+[a-z]?-[IR]-')
# print(f"\nTrips con formato normal (route-dir-service-Bxx): {patron_normal.sum()}")
# print(f"Trips con formato distinto: {(~patron_normal).sum()}")
# print(trips[~patron_normal]['trip_id'].head(10))
# print(trips[~patron_normal]['route_id'].value_counts().head(10))


def time_to_min(t):
    h, m, s = map(int, t.split(':'))
    return h*60 + m + s/60

freq['start_min'] = freq['start_time'].apply(time_to_min)
freq['end_min'] = freq['end_time'].apply(time_to_min)
freq['duracion_ventana_min'] = freq['end_min'] - freq['start_min']

# Ojo: duracion_ventana_seg debe estar en segundos para dividir por headway_secs
freq['num_salidas'] = (freq['duracion_ventana_min'] * 60) / freq['headway_secs']

print(freq['num_salidas'].describe())
print(f"\nTotal de salidas reales (expandiendo por headway): {freq['num_salidas'].sum():.0f}")

# Ventanas sospechosas (duración <= 0, indicaría cruce de medianoche mal manejado)
print(f"\nVentanas con duración <= 0 min: {(freq['duracion_ventana_min'] <= 0).sum()}")

# Ahora sí, la segunda familia de trip_id
import re
patron_normal = trips['trip_id'].str.match(r'^\w+-[IR]-')
print(f"\nTrips con formato normal: {patron_normal.sum()}")
print(f"Trips con formato distinto: {(~patron_normal).sum()}")
print(trips[~patron_normal]['trip_id'].head(10))
print(trips[~patron_normal]['route_id'].value_counts().head(10))