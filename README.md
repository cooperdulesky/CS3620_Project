# SproutLog: Smart Garden Manager

## Project Goal
SproutLog is a data-driven gardening management application designed to help users track their plant inventory and monitor growing conditions. By integrating specific garden data with public biological and environmental datasets, the app provides intelligent insights—such as correlating plant growth with historical weather patterns and analyzing potential disease risks based on daily environmental logs.

## Interaction Description
The application provides a command-line interface (CLI) for the checkpoint demonstration:
1.  **User Onboarding:** Users create secure accounts with password hashing and location data (Zip Code).
2.  **Dynamic Geocoding:** The app uses the **Zippopotam.us API** to convert user Zip Codes into precise Latitude/Longitude coordinates automatically.
3.  **Inventory Management:** Users browse the imported **USDA** plant database and "plant" species in their virtual gardens.
4.  **Environmental Logging:** The system automatically fetches real-time daily weather (Max/Min/Rain) via the **Open-Meteo API** and logs it to the database to create a historical record of growing conditions.

## Public Datasets Used
1.  **USDA PLANTS Database:**
    * **Type:** CSV Import (Reference Data)
    * **Usage:** Created a much smaller table of only about 30 common plants because I felt much of the giant database would go unused. Populates the `ref_species` table with scientific names, common names, and families to ensure accurate plant identification.
    * **Link:** https://plants.usda.gov/downloads
2.  **Open-Meteo API:**
    * **Type:** REST API (Public Domain)
    * **Usage:** Daily weather metrics (Temperature, Rainfall, Wind) are ingested into the `bg_weather_daily` table to track environmental history for every user location.
    * **Link:** https://open-meteo.com
3.  **Plant Disease Environmental Model:**
    * **Type:** CSV Import (Kaggle Dataset)
    * **Usage:** Populates `ref_disease_model` to correlate specific temperature/humidity ranges with the likelihood of plant diseases.
    * **Link:** https://www.kaggle.com/datasets/turakut/plant-disease-classification

## How to Run
1.  **Database Setup:** Import the `schema.sql` file into your MySQL server to create the 12 tables.
2.  **Install Dependencies:**
    ```bash
    pip install mysql-connector-python requests
    ```
3.  **Configure:** Update the `db_config` dictionary in `app.py` with your local MySQL password.
4.  **Run:**
    ```bash
    python app.py
    ```

## Database Schema
The database consists of 12 tables organized into Core Data, Reference Data, Operational Logs, and Gamification.

```mermaid
erDiagram
    USERS {
        int user_id PK
        string email
        string display_name
        string zip_code
    }
    SESSIONS {
        int session_id PK
        int user_id FK
        string token
    }
    ALERTS {
        int alert_id PK
        int user_id FK
        string message
    }
    GARDENS {
        int garden_id PK
        int user_id FK
        string name
    }
    PLANTS_INVENTORY {
        int inventory_id PK
        int garden_id FK
        int species_id FK
        string nickname
    }
    REF_SPECIES {
        int species_id PK
        string common_name
        string scientific_name
    }
    CARE_LOGS {
        int log_id PK
        int inventory_id FK
        string action_type
    }
    HARVESTS {
        int harvest_id PK
        int inventory_id FK
        int quantity
    }
    BG_WEATHER_DAILY {
        int weather_id PK
        string zip_code
        date record_date
        float temp_max_f
    }
    REF_DISEASE_MODEL {
        int model_id PK
        float temperature
        float humidity
        int disease_present
    }
    COMMUNITY_CHALLENGES {
        int challenge_id PK
        string title
    }
    USER_CHALLENGES {
        int user_id FK
        int challenge_id FK
        string status
    }

    %% Hard Relationships (Foreign Keys)
    USERS ||--o{ GARDENS : owns
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ ALERTS : receives
    USERS ||--o{ USER_CHALLENGES : joins
    COMMUNITY_CHALLENGES ||--o{ USER_CHALLENGES : defined_by
    
    GARDENS ||--o{ PLANTS_INVENTORY : contains
    REF_SPECIES ||--o{ PLANTS_INVENTORY : classifies
    
    PLANTS_INVENTORY ||--o{ CARE_LOGS : records
    PLANTS_INVENTORY ||--o{ HARVESTS : yields

    %% Logical Relationships (Analysis)
    USERS }|..|{ BG_WEATHER_DAILY : "located_in (zip)"
    BG_WEATHER_DAILY }|..|{ REF_DISEASE_MODEL : "analyzed_against"
