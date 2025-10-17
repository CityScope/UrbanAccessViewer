import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Address Finder", page_icon="📍", layout="centered")
st.title("📍 Address Finder on the Map")

# --- States ---
if "map_data" not in st.session_state:
    st.session_state.map_data = None
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "confirmed_address" not in st.session_state:
    st.session_state.confirmed_address = None
if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# --- Función de sugerencias ---
def get_suggestions(query):
    if not query or len(query) < 3:
        return []
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 5, "addressdetails": 1}
    headers = {"User-Agent": "streamlit-map-app/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [d["display_name"] for d in data]
    except:
        return []
    return []

# --- Input ---
address = st.text_input("Enter an address:", placeholder="Example: New York, USA")

if address != st.session_state.last_input:
    st.session_state.confirmed_address = None
    st.session_state.map_data = None
    st.session_state.last_input = address

# --- Suggestions ---
if address and not st.session_state.confirmed_address:
    st.session_state.suggestions = get_suggestions(address)
else:
    st.session_state.suggestions = []

if st.session_state.suggestions:
    st.write("🔎 **Suggestions:**")
    for i, sug in enumerate(st.session_state.suggestions):
        if st.button(sug, key=f"sug-{i}"):
            st.session_state.confirmed_address = sug
            st.session_state.suggestions = []

            # Obtener coordenadas
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": sug, "format": "json", "limit": 1}
            headers = {"User-Agent": "streamlit-map-app/1.0"}
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        lat = float(data[0]["lat"])
                        lon = float(data[0]["lon"])
                        display_name = data[0]["display_name"]
                        st.session_state.map_data = {
                            "lat": lat,
                            "lon": lon,
                            "display_name": display_name,
                            "address": sug,
                        }
            except Exception as e:
                st.error(f"Error connecting to the API: {e}")

# --- Enter ---
if address and not st.session_state.suggestions and not st.session_state.map_data and not st.session_state.confirmed_address:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "streamlit-map-app/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display_name = data[0]["display_name"]
                st.session_state.map_data = {
                    "lat": lat,
                    "lon": lon,
                    "display_name": display_name,
                    "address": address,
                }
                st.session_state.confirmed_address = address
            else:
                st.warning("Address not found.")
    except Exception as e:
        st.error(f"Error connecting to the API: {e}")

# --- Show map ---
if st.session_state.map_data:
    lat = st.session_state.map_data["lat"]
    lon = st.session_state.map_data["lon"]
    display_name = st.session_state.map_data["display_name"]
    address = st.session_state.map_data["address"]

    st.success(f"Address found: {display_name}")
    st.write(f"🌍 Coordinates: ({lat:.5f}, {lon:.5f})")

    map_ = folium.Map(location=[lat, lon], zoom_start=5)

    # Marker
    folium.Marker([lat, lon], popup=address, tooltip="Location").add_to(map_)

    # US population TileLayer
    folium.TileLayer(
        tiles="http://localhost:8000/tiles/{z}/{x}/{y}.png",
        attr="US Population",
        name="Population",
        overlay=True,
        control=True,
        opacity=0.6
    ).add_to(map_)

    folium.LayerControl().add_to(map_)
    st_folium(map_, width=800, height=500)
