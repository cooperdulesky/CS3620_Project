import mysql.connector
import requests
from datetime import date

# --- CONFIGURATION ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Boogers4bear',
    'database': 'SproutLog'
}

def get_lat_lon_from_zip(zip_code):
    """
    Converts a US Zip Code to Latitude/Longitude using Zippopotam.us (Free/No Key)
    """
    try:
        url = f"http://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url)
        
        if response.status_code == 404:
            print(f"   ⚠️  Warning: Zip Code {zip_code} not found. Defaulting to Athens, OH.")
            return (39.32, -82.10) # Default fallback

        data = response.json()
        # The API returns a list of places. We take the first one.
        place = data['places'][0]
        lat = float(place['latitude'])
        lon = float(place['longitude'])
        city = place['place name']
        state = place['state abbreviation']
        
        print(f"   📍 Located: {city}, {state} ({lat}, {lon})")
        return (lat, lon)

    except Exception as e:
        print(f"Geocoding Error: {e}")
        return (39.32, -82.10) # Fallback if internet fails

def get_daily_weather(lat, lon):
    """Fetches DAILY weather summary (Max, Min, Rain)"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, 
            "longitude": lon, 
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto"
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        daily = data['daily']
        return {
            'max': daily['temperature_2m_max'][0],
            'min': daily['temperature_2m_min'][0],
            'rain': daily['precipitation_sum'][0],
            'wind': daily['wind_speed_10m_max'][0]
        }
    except Exception as e:
        print(f"Weather Error: {e}")
        return None

def run_app():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("\n🌱 --- SPROUTLOG: NEW USER SIGNUP --- 🌱")

        # 1. User Signup
        email = input("Enter email address: ")
        display_name = input("Enter display name: ") 
        password = input("Create password: ")
        zip_code = input("Enter Zip Code: ") 
        
        cursor.execute("INSERT INTO users (email, display_name, password_hash, zip_code) VALUES (%s, %s, %s, %s)", 
                       (email, display_name, password, zip_code))
        user_id = cursor.lastrowid
        print(f"✅ User '{display_name}' created! (ID: {user_id})")

        # 2. Create Garden
        garden_name = input("\nName your first garden: ")
        cursor.execute("INSERT INTO gardens (user_id, name) VALUES (%s, %s)", (user_id, garden_name))
        garden_id = cursor.lastrowid
        print(f"✅ Garden '{garden_name}' established.")

        # 3. Interactive Plant Menu
        print("\n--- SELECT A CROP TO PLANT ---")
        cursor.execute("SELECT species_id, common_name, scientific_name FROM ref_species")
        plants = cursor.fetchall()
        for p in plants:
            print(f"{p[0]}. {p[1]} ({p[2]})")   
        selected_id = input("\nEnter the ID number of the plant you want: ")
        
        cursor.execute("INSERT INTO plants_inventory (garden_id, species_id, nickname, date_planted) VALUES (%s, %s, %s, %s)", 
                       (garden_id, selected_id, "My New Crop", date.today()))
        print("✅ Seed planted in inventory.")

        # 4. Fetch REAL Weather (Dynamic!)
        print("\n☁️  Connecting to Weather Satellite...")
        
        # DYNAMIC STEP: Convert Zip to Lat/Lon using API
        lat, lon = get_lat_lon_from_zip(zip_code)

        weather = get_daily_weather(lat, lon)
        
        if weather:
            print(f"   Today's Forecast: High {weather['max']}°F / Low {weather['min']}°F")
            print(f"   Rainfall: {weather['rain']} inches")
            
            sql = """INSERT INTO bg_weather_daily 
                     (zip_code, record_date, temp_max_f, temp_min_f, precipitation_inches, wind_speed_mph) 
                     VALUES (%s, CURRENT_DATE, %s, %s, %s, %s)
                     ON DUPLICATE KEY UPDATE 
                     temp_max_f = %s, temp_min_f = %s, precipitation_inches = %s, wind_speed_mph = %s"""
            
            cursor.execute(sql, (
                zip_code, weather['max'], weather['min'], weather['rain'], weather['wind'], 
                weather['max'], weather['min'], weather['rain'], weather['wind']
            ))
            print("✅ Daily environment log saved.")

        conn.commit()
        print("\n🎉 DEMO COMPLETE: Data successfully written to 4 tables.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_app()