import requests
import json
import math
from flask import Flask, request, jsonify

app = Flask(__name__)

# URL de la API de WordPress (Fuente de datos)
API_URL = "https://ilikehuila.com/wp-json/wp/v2/job-listings"

# Función para obtener los datos de la API
def obtener_datos_json():
    try:
        respuesta = requests.get(API_URL)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al obtener datos: {e}"}

# Función para calcular la distancia entre dos puntos geográficos
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Ruta principal (prueba si el servidor funciona)
@app.route("/")
def home():
    return "¡Servidor funcionando en Render!"

# Ruta para buscar sitios turísticos por nombre o palabra clave
@app.route("/buscar", methods=["GET"])
def buscar():
    consulta = request.args.get("query", "").lower()
    if not consulta:
        return jsonify({"error": "Por favor proporciona un parámetro 'query'."})

    datos_json = obtener_datos_json()
    if "error" in datos_json:
        return jsonify(datos_json)

    resultados = []
    for sitio in datos_json:
        if any(consulta in str(valor).lower() for clave, valor in sitio.items() if isinstance(valor, str)):
            meta = sitio.get("meta", {})
            resultados.append({
                "nombre": sitio.get("title", {}).get("rendered", "Nombre no disponible"),
                "ubicacion": meta.get("ubicacion", "No especificada"),
                "direccion": meta.get("geolocation_formatted_address", "No especificada"),
                "categoria": meta.get("categoria", "No especificada"),
                "telefono": meta.get("company_phone", "No especificado"),
                "celular": meta.get("company_mobile", "No especificado"),
                "website": meta.get("company_website", "No especificado"),
                "facebook": meta.get("company_facebook", "No especificado"),
                "instagram": meta.get("company_instagram", "No especificado"),
                "tiktok": meta.get("company_tiktok", "No especificado"),
                "tripadvisor": meta.get("company_tripadvisor", "No especificado"),
                "whatsapp": f"https://wa.me/{meta.get('company_whatsapp', '')}" if meta.get("company_whatsapp") else "No disponible",
                "link_perfil": meta.get("link", "No disponible"),
                "latitud": meta.get("geolocation_lat", None),
                "longitud": meta.get("geolocation_long", None),
                "mapa_google": f"https://www.google.com/maps?q={meta.get('geolocation_lat')},{meta.get('geolocation_long')}" if meta.get("geolocation_lat") and meta.get("geolocation_long") else "No disponible"
            })
    
    return jsonify(resultados if resultados else {"mensaje": "No se encontraron sitios turísticos."})

# Ruta para buscar los 5 sitios turísticos más cercanos
@app.route("/cerca", methods=["GET"])
def buscar_cercano():
    try:
        lat_usuario = float(request.args.get("lat"))
        lon_usuario = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Proporcione latitud y longitud válidas como parámetros 'lat' y 'lon'."})

    datos_json = obtener_datos_json()
    if "error" in datos_json:
        return jsonify(datos_json)

    lugares_con_distancia = []
    for sitio in datos_json:
        meta = sitio.get("meta", {})
        latitud = meta.get("geolocation_lat")
        longitud = meta.get("geolocation_long")
        if latitud and longitud:
            distancia = calcular_distancia(lat_usuario, lon_usuario, float(latitud), float(longitud))
            lugares_con_distancia.append({
                "nombre": sitio.get("title", {}).get("rendered", "Nombre no disponible"),
                "ubicacion": meta.get("ubicacion", "No especificada"),
                "direccion": meta.get("geolocation_formatted_address", "No especificada"),
                "telefono": meta.get("company_phone", "No especificado"),
                "distancia_km": round(distancia, 2),
                "mapa_google": f"https://www.google.com/maps?q={latitud},{longitud}"
            })
    
    lugares_con_distancia.sort(key=lambda x: x["distancia_km"])
    return jsonify(lugares_con_distancia[:5] if lugares_con_distancia else {"mensaje": "No se encontraron lugares cercanos."})

# Iniciar la aplicación
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
