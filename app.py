import re
from flask import Flask, render_template, request
import requests
import math

app = Flask(__name__)

# Open Charge Map API key
API_KEY = "d4f80b55-bbfc-49ad-908e-e016432fc799"
API_URL = "https://api.openchargemap.io/v3/poi/"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formülü ile mesafe hesaplama"""
    R = 6371  # Dünya'nın yarıçapı (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            user_lat = request.form.get("latitude")
            user_lon = request.form.get("longitude")
            
            print("Gelen Konum Verisi:", user_lat, user_lon)  # Terminale yazdır
            
            if not user_lat or not user_lon:
                return render_template('index.html', stations=[], error="Konum bilgisi alınamadı.")

            user_lat = float(user_lat)
            user_lon = float(user_lon)

            params = {
                'key': API_KEY,
                'output': 'json',
                'latitude': user_lat,
                'longitude': user_lon,
                'distance': 50,
                'distanceunit': 'KM',
                'maxresults': 20
            }
            response = requests.get(API_URL, params=params)
            print("API Yanıt Kodu:", response.status_code)
            print("API Yanıtı:", response.text[:500])  # İlk 500 karakterini yazdır

            if response.status_code != 200:
                return render_template('index.html', stations=[], error="API bağlantı hatası.")

            stations = response.json()
            if not stations:
                return render_template('index.html', stations=[], error="Şarj istasyonu bulunamadı.")

            # Mesafeye göre sırala ve varış süresi hesapla
            for station in stations:
                station_lat = station['AddressInfo']['Latitude']
                station_lon = station['AddressInfo']['Longitude']
                station['distance'] = calculate_distance(user_lat, user_lon, station_lat, station_lon)
                station['eta'] = round((station['distance'] / 60) * 60)  # Dakika cinsinden
                
                # Connections bilgilerini kontrol et
                for connection in station.get('Connections', []):  # Connections varsa devam et
                    connection_info = []

                    connection_type = connection['ConnectionType']['Title'] if connection.get('ConnectionType') else None
                    power_kw = connection.get('PowerKW', None)
                    current_type = connection['CurrentType']['Title'] if connection.get('CurrentType') else None  # AC/DC bilgisini al

                    if current_type:  # Eğer AC/DC bilgisi varsa önce onu ekle
                        connection_info.append(current_type)
                    elif power_kw:  # Son çare olarak kW değerini ekle
                        connection_info.append(f"{power_kw} kW")
                    elif connection_type:  # Sonra soket tipini ekle
                        connection_info.append(connection_type)

                    station['connection_info'] = ", ".join(connection_info) if connection_info else None
            
            stations.sort(key=lambda x: x['distance'])
            return render_template('index.html', stations=stations)
        
        except Exception as e:
            print("Hata:", e)
            return render_template('index.html', stations=[], error="Beklenmeyen bir hata oluştu.")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
