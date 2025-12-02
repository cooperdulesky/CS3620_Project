import tkinter as tk
from tkinter import ttk, messagebox
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

# --- API HELPER FUNCTIONS ---
def get_lat_lon_from_zip(zip_code):
    try:
        url = f"http://api.zippopotam.us/us/{zip_code}"
        response = requests.get(url)
        if response.status_code == 404: return (39.32, -82.10, "Unknown") # Default Athens
        data = response.json()
        place = data['places'][0]
        return float(place['latitude']), float(place['longitude']), place['place name']
    except:
        return (39.32, -82.10, "Unknown")

def get_daily_weather(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon, 
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch",
            "timezone": "auto"
        }
        res = requests.get(url, params=params).json()['daily']
        return {
            'max': res['temperature_2m_max'][0], 'min': res['temperature_2m_min'][0],
            'rain': res['precipitation_sum'][0], 'wind': res['wind_speed_10m_max'][0]
        }
    except:
        return None

# --- MAIN GUI CLASS ---
class SproutLogGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SproutLog Manager")
        self.root.geometry("900x700")
        
        # Connect to DB
        try:
            self.conn = mysql.connector.connect(**db_config)
            self.cursor = self.conn.cursor()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to DB: {e}")
            return

        # Start with the Login Screen
        self.show_login_screen()

    # ===========================
    # PART 1: LOGIN & ONBOARDING
    # ===========================
    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="#e8f5e9")
        self.login_frame.pack(fill="both", expand=True)

        # Title
        tk.Label(self.login_frame, text="🌱 SproutLog", font=("Helvetica", 32, "bold"), bg="#e8f5e9", fg="#2e7d32").pack(pady=(60, 10))
        # Subtitle
        tk.Label(self.login_frame, text="Garden Management System", font=("Arial", 14), bg="#e8f5e9", fg="#444444").pack(pady=10)

        # Form Container
        form = tk.Frame(self.login_frame, bg="white", padx=40, pady=40, relief="raised")
        form.pack(pady=20)

        # --- UPDATED LABELS (Forced Black Text for Mac Dark Mode) ---
        tk.Label(form, text="Email Address:", bg="white", fg="black", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.ent_email = ttk.Entry(form, width=30)
        self.ent_email.grid(row=0, column=1, pady=10)

        tk.Label(form, text="Display Name:", bg="white", fg="black", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        self.ent_name = ttk.Entry(form, width=30)
        self.ent_name.grid(row=1, column=1, pady=10)

        tk.Label(form, text="Create Password:", bg="white", fg="black", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        self.ent_pass = ttk.Entry(form, width=30, show="*")
        self.ent_pass.grid(row=2, column=1, pady=10)

        tk.Label(form, text="Zip Code (for Weather):", bg="white", fg="black", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        self.ent_zip = ttk.Entry(form, width=30)
        self.ent_zip.grid(row=3, column=1, pady=10)

        # Button
        ttk.Button(form, text="ENTER GARDEN ➤", command=self.process_login).grid(row=4, column=1, pady=20, sticky="ew")

    def process_login(self):
        email = self.ent_email.get()
        name = self.ent_name.get()
        password = self.ent_pass.get()
        zip_code = self.ent_zip.get()

        if not email or not name or not zip_code:
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            # 1. Create User
            self.cursor.execute("INSERT INTO users (email, display_name, password_hash, zip_code) VALUES (%s, %s, %s, %s)", 
                                (email, name, password, zip_code))
            self.conn.commit()
            self.user_id = self.cursor.lastrowid
            
            # 2. Create Default Gardens
            gardens = ["Backyard", "Front Yard", "Porch", "Greenhouse"]
            for g in gardens:
                self.cursor.execute("INSERT INTO gardens (user_id, name) VALUES (%s, %s)", (self.user_id, g))
            self.conn.commit()

            # 3. Get Weather Data
            self.current_zip = zip_code
            res = get_lat_lon_from_zip(zip_code)
            lat, lon, city_name = res
            self.weather_data = get_daily_weather(lat, lon)
            self.location_name = city_name

            # 4. Save Weather to DB
            if self.weather_data:
                sql = """INSERT INTO bg_weather_daily 
                         (zip_code, record_date, temp_max_f, temp_min_f, precipitation_inches, wind_speed_mph) 
                         VALUES (%s, CURRENT_DATE, %s, %s, %s, %s)
                         ON DUPLICATE KEY UPDATE temp_max_f=%s"""
                self.cursor.execute(sql, (zip_code, self.weather_data['max'], self.weather_data['min'], 
                                          self.weather_data['rain'], self.weather_data['wind'], self.weather_data['max']))
                self.conn.commit()

            # 5. Switch Screens
            self.login_frame.destroy()
            self.show_main_dashboard()

        except Exception as e:
            # If email duplicates, just fetch the existing user
            if "Duplicate entry" in str(e):
                self.cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                self.user_id = self.cursor.fetchone()[0]
                self.current_zip = zip_code
                self.location_name = "Existing User Location"
                self.weather_data = None # Skip weather for simplicity on re-login
                self.login_frame.destroy()
                self.show_main_dashboard()
            else:
                messagebox.showerror("Login Error", str(e))

    # ===========================
    # PART 2: MAIN DASHBOARD
    # ===========================
    def show_main_dashboard(self):
        # --- Top Banner (Weather) ---
        banner = tk.Frame(self.root, bg="#2196f3", height=80)
        banner.pack(fill="x", side="top")
        
        # Weather Text
        if self.weather_data:
            w_text = f"📍 {self.location_name} ({self.current_zip})  |  🌡️ High: {self.weather_data['max']}°F  Low: {self.weather_data['min']}°F  |  🌧️ Rain: {self.weather_data['rain']} in"
        else:
            w_text = "Weather Data Unavailable"
            
        tk.Label(banner, text=w_text, font=("Arial", 14, "bold"), bg="#2196f3", fg="white").pack(pady=20)

        # --- Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        self.frame_inventory = ttk.Frame(self.notebook)
        self.frame_add = ttk.Frame(self.notebook)
        
        self.notebook.add(self.frame_inventory, text="My Garden Inventory")
        self.notebook.add(self.frame_add, text="Add New Plant")

        self.setup_inventory_tab()
        self.setup_add_tab()

    def setup_inventory_tab(self):
        filter_frame = ttk.LabelFrame(self.frame_inventory, text="Filter Options")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Search Nickname:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Filter", command=self.refresh_table).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Clear", command=self.clear_filter).pack(side="left", padx=5)

        columns = ("ID", "Nickname", "Species", "Planted Date", "Status", "Location")
        self.tree = ttk.Treeview(self.frame_inventory, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self.frame_inventory)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Mark as Harvested (Update)", command=self.update_status).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Plant", command=self.delete_plant).pack(side="right", padx=5)
        
        self.refresh_table()

    def setup_add_tab(self):
        form_frame = ttk.Frame(self.frame_add, padding=40)
        form_frame.pack(fill="both", expand=True)
        
        ttk.Label(form_frame, text="Plant Nickname:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=10)
        self.entry_nickname = ttk.Entry(form_frame, font=("Arial", 12))
        self.entry_nickname.grid(row=0, column=1, sticky="ew", pady=10)
        
        ttk.Label(form_frame, text="Select Species:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=10)
        self.cursor.execute("SELECT species_id, common_name FROM ref_species")
        self.species_map = {name: pid for pid, name in self.cursor.fetchall()}
        self.combo_species = ttk.Combobox(form_frame, values=list(self.species_map.keys()), state="readonly", font=("Arial", 12))
        self.combo_species.set("Choose Species...") 
        self.combo_species.grid(row=1, column=1, sticky="ew", pady=10)

        ttk.Label(form_frame, text="Select Location:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=10)
        # Reload gardens to check for user specific ones
        self.cursor.execute("SELECT garden_id, name FROM gardens WHERE user_id=%s", (self.user_id,))
        self.garden_map = {name: gid for gid, name in self.cursor.fetchall()}
        self.combo_garden = ttk.Combobox(form_frame, values=list(self.garden_map.keys()), state="readonly", font=("Arial", 12))
        self.combo_garden.set("Choose Garden...") 
        self.combo_garden.grid(row=2, column=1, sticky="ew", pady=10)
        
        ttk.Button(form_frame, text="🌱 PLANT IT", command=self.create_plant).grid(row=3, column=1, pady=30, sticky="ew")

    # --- CRUD FUNCTIONS ---
    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        search_term = self.search_var.get()
        query = """
            SELECT p.inventory_id, p.nickname, r.common_name, p.date_planted, p.status, g.name 
            FROM plants_inventory p
            JOIN ref_species r ON p.species_id = r.species_id
            JOIN gardens g ON p.garden_id = g.garden_id
            WHERE p.nickname LIKE %s
            ORDER BY p.inventory_id ASC
        """
        self.cursor.execute(query, (f"%{search_term}%",))
        for row in self.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def clear_filter(self):
        self.search_var.set("")
        self.refresh_table()

    def create_plant(self):
        try:
            nick = self.entry_nickname.get()
            spec_name = self.combo_species.get()
            gard_name = self.combo_garden.get()
            if spec_name == "Choose Species..." or gard_name == "Choose Garden...":
                messagebox.showwarning("Missing Info", "Please select a valid Species and Garden.")
                return
            if not nick:
                messagebox.showerror("Error", "Please enter a nickname.")
                return

            spec_id = self.species_map[spec_name]
            gard_id = self.garden_map[gard_name]
            sql = "INSERT INTO plants_inventory (garden_id, species_id, nickname, date_planted, status) VALUES (%s, %s, %s, %s, 'Growing')"
            self.cursor.execute(sql, (gard_id, spec_id, nick, date.today()))
            self.conn.commit()
            messagebox.showinfo("Success", f"{nick} planted!")
            self.entry_nickname.delete(0, 'end')
            self.refresh_table()
            self.notebook.select(0) 
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def update_status(self):
        selected = self.tree.selection()
        if not selected: return
        plant_id = self.tree.item(selected[0])['values'][0]
        self.cursor.execute("UPDATE plants_inventory SET status = 'Harvested' WHERE inventory_id = %s", (plant_id,))
        self.conn.commit()
        self.refresh_table()

    def delete_plant(self):
        selected = self.tree.selection()
        if not selected: return
        plant_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this plant?"):
            self.cursor.execute("DELETE FROM plants_inventory WHERE inventory_id = %s", (plant_id,))
            self.conn.commit()
            # SMART RESET ID
            self.cursor.execute("SELECT COUNT(*) FROM plants_inventory")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("ALTER TABLE plants_inventory AUTO_INCREMENT = 1")
                self.conn.commit()
            self.refresh_table()

if __name__ == "__main__":
    root = tk.Tk()
    app = SproutLogGUI(root)
    root.mainloop()