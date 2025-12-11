# SproutLog: Smart Garden Manager

## Project Goal
SproutLog is a data-driven gardening management application designed to help users track their plant inventory, monitor growing conditions, and manage gardening resources. By integrating specific garden data with public biological and environmental datasets, the app provides intelligent insights—such as correlating plant growth with historical weather patterns and analyzing potential disease risks based on daily environmental logs.

## Application Features (GUI)
The application has been upgraded from a CLI to a full **Graphical User Interface (GUI)** built with Python/Tkinter.
* **User Authentication:** Secure login screen with password hashing and automatic account creation.
* **Dynamic Geocoding:** Integrates the **Zippopotam.us API** to auto-detect location coordinates from Zip Codes.
* **Live Weather:** Integrates the **Open-Meteo API** to fetch and log daily weather metrics (Temp/Rain) for the user's specific location.
* **Garden Management:** dedicated interface to manage garden details (Length, Width, Sun Exposure) for specific locations (Backyard, Greenhouse, etc.).
* **Inventory Management (CRUD):**
    * **Create:** "Plant" new crops by selecting from the USDA reference database.
    * **Read:** View all plants with sorting and filtering options.
    * **Update:** Mark plants as "Harvested" to track status changes.
    * **Delete:** Remove plants (with auto-resetting ID logic for clean demos).
    * **Filter:** Real-time search bar to find plants by nickname.
* **Health & Analytics:**
    * **Health Reporting:** Log specific sickness events (bugs, mold) with severity levels.
    * **Yield Analytics:** A dedicated dashboard tab showing aggregated crop performance (Mart Data).
    * **Auditing:** Background system logging for all critical user actions (Inserts/Deletes/Updates).

## Public Datasets Used
1.  **USDA PLANTS Database:**
    * **Type:** CSV Import (Reference Data)
    * **Usage:** Created a curated table of ~30 common garden plants (reduced from the full dataset for performance). Populates the `ref_species` table with scientific names, common names, and families.
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
1.  **Database Setup:** Import the `schema.sql` file into your MySQL server to create the 23 tables.
2.  **Install Dependencies:**
    ```bash
    pip install mysql-connector-python requests
    ```
3.  **Configure:** Update the `db_config` dictionary in `gui_app.py` with your local MySQL password.
4.  **Run:**
    ```bash
    python gui_app.py
    ```

## Database Schema (23 Tables)
The database structure supports Core Users, Inventory, Finance, Tools, Social, and Analytics.

```mermaid
erDiagram
    %% --- CORE USER & LOCATIONS ---
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
        float length_ft
        float width_ft
        string sun_exposure
    }
    SYSTEM_AUDIT_LOG {
        int audit_id PK
        int user_id FK
        string action_type
        string table_affected
    }

    %% --- INVENTORY & OPERATIONS ---
    PLANTS_INVENTORY {
        int inventory_id PK
        int garden_id FK
        int species_id FK
        string nickname
        string status
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
    PLANT_HEALTH_EVENTS {
        int event_id PK
        int inventory_id FK
        string issue_type
        int severity
    }

    %% --- REFERENCE DATA ---
    REF_SPECIES {
        int species_id PK
        string common_name
        string scientific_name
    }
    BG_WEATHER_DAILY {
        int weather_id PK
        string zip_code
        float temp_max_f
        float precipitation_inches
    }
    REF_DISEASE_MODEL {
        int model_id PK
        float temperature
        float humidity
        int disease_present
    }
    MART_YIELD_ANALYTICS {
        int mart_id PK
        int species_id FK
        int total_yield_count
    }

    %% --- FINANCES & SUPPLIERS ---
    SUPPLIERS {
        int supplier_id PK
        string name
        int rating
    }
    EXPENSES {
        int expense_id PK
        int user_id FK
        int supplier_id FK
        float amount
    }

    %% --- TOOLS & RESOURCES ---
    REF_TOOL_TYPES {
        int type_id PK
        string category
        string tool_name
    }
    USER_TOOLS {
        int tool_instance_id PK
        int user_id FK
        int type_id FK
        string condition
    }
    REF_FERTILIZERS {
        int fertilizer_id PK
        string name
        string npk_ratio
    }
    PLANT_FERTILIZER_LINK {
        int link_id PK
        int inventory_id FK
        int fertilizer_id FK
        date next_due
    }

    %% --- SOCIAL & GAMIFICATION ---
    SOCIAL_POSTS {
        int post_id PK
        int user_id FK
        string content_text
    }
    POST_COMMENTS {
        int comment_id PK
        int post_id FK
        int user_id FK
        string comment_text
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

    %% --- RELATIONSHIPS ---
    
    %% User Ownership
    USERS ||--o{ GARDENS : owns
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ ALERTS : receives
    USERS ||--o{ EXPENSES : incurs
    USERS ||--o{ USER_TOOLS : owns
    USERS ||--o{ SOCIAL_POSTS : creates
    USERS ||--o{ POST_COMMENTS : writes
    USERS ||--o{ USER_CHALLENGES : participates_in
    USERS ||--o{ SYSTEM_AUDIT_LOG : generates

    %% Inventory Logic
    GARDENS ||--o{ PLANTS_INVENTORY : contains
    REF_SPECIES ||--o{ PLANTS_INVENTORY : classifies
    PLANTS_INVENTORY ||--o{ CARE_LOGS : requires
    PLANTS_INVENTORY ||--o{ HARVESTS : produces
    PLANTS_INVENTORY ||--o{ PLANT_FERTILIZER_LINK : treated_with
    PLANTS_INVENTORY ||--o{ PLANT_HEALTH_EVENTS : suffers

    %% Analytics & Marts
    REF_SPECIES ||--o{ MART_YIELD_ANALYTICS : aggregated_in

    %% Finances & Tools
    SUPPLIERS ||--o{ EXPENSES : paid_to
    REF_TOOL_TYPES ||--o{ USER_TOOLS : describes
    REF_FERTILIZERS ||--o{ PLANT_FERTILIZER_LINK : describes

    %% Social & Games
    SOCIAL_POSTS ||--o{ POST_COMMENTS : receives
    COMMUNITY_CHALLENGES ||--o{ USER_CHALLENGES : defines

    %% Analytical Links (Logical)
    USERS }|..|{ BG_WEATHER_DAILY : "located_in"
    BG_WEATHER_DAILY }|..|{ REF_DISEASE_MODEL : "analyzed_against"
