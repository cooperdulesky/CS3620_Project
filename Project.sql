CREATE DATABASE SproutLog;
USE SproutLog;

-- --- SECTION 1: CORE APP DATA (Users & Gardens) ---

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(50),
    zip_code VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gardens (
    garden_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    length_ft DECIMAL(5,2),
    width_ft DECIMAL(5,2),
    sun_exposure ENUM('Full Sun', 'Partial Shade', 'Full Shade'),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- --- SPECIFIC DATASETS ---

CREATE TABLE ref_species (
    species_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    synonym_symbol VARCHAR(20),
    scientific_name VARCHAR(255),
    common_name VARCHAR(255),
    family_name VARCHAR(100)
);

CREATE TABLE ref_disease_model (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    temperature FLOAT,
    humidity FLOAT,
    rainfall FLOAT,
    soil_ph FLOAT,
    disease_present INT -- 0 or 1
);

-- --- OPEN-METEO DATA ---
CREATE TABLE bg_weather_daily (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    zip_code VARCHAR(10),
    record_date DATE,
    temp_max_f DECIMAL(5,2),
    temp_min_f DECIMAL(5,2),
    precipitation_inches DECIMAL(5,2),
    wind_speed_mph DECIMAL(5,2),
    UNIQUE KEY (zip_code, record_date)
);

-- --- USER INTERACTIONS (Write Tables) ---
CREATE TABLE plants_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    garden_id INT NOT NULL,
    species_id INT, -- Links to your USDA table
    nickname VARCHAR(50),
    date_planted DATE,
    status ENUM('Seed', 'Growing', 'Harvested', 'Dead') DEFAULT 'Growing',
    FOREIGN KEY (garden_id) REFERENCES gardens(garden_id) ON DELETE CASCADE,
    FOREIGN KEY (species_id) REFERENCES ref_species(species_id)
);

CREATE TABLE care_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_id INT NOT NULL,
    action_type ENUM('Water', 'Fertilize', 'Prune', 'Treat Pest'),
    notes TEXT,
    log_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inventory_id) REFERENCES plants_inventory(inventory_id) ON DELETE CASCADE
);

CREATE TABLE harvests (
    harvest_id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_id INT NOT NULL,
    quantity INT,
    weight_grams DECIMAL(8,2),
    quality_rating INT,
    harvest_date DATE,
    FOREIGN KEY (inventory_id) REFERENCES plants_inventory(inventory_id)
);

-- --- GAMIFICATION ---
CREATE TABLE community_challenges (
    challenge_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100),
    goal_description TEXT,
    start_date DATE,
    end_date DATE
);

CREATE TABLE user_challenges (
    user_id INT,
    challenge_id INT,
    status ENUM('Joined', 'In Progress', 'Completed') DEFAULT 'Joined',
    progress_percent INT DEFAULT 0,
    PRIMARY KEY (user_id, challenge_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (challenge_id) REFERENCES community_challenges(challenge_id)
);

-- --- EXTRAS (Tables 11 & 12) ---
-- Table 11: To track user logins
CREATE TABLE sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Table 12: To store system warnings (Frost, Pests, etc.)
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    alert_type VARCHAR(50), -- e.g., 'Frost Warning'
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- show tables for demo
SELECT * FROM users;
SELECT * FROM bg_weather_daily;
SELECT * FROM gardens;
SELECT * FROM plants_inventory;

-- Clear the 4 tables the script touches
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE plants_inventory;
TRUNCATE TABLE gardens;
TRUNCATE TABLE users;
TRUNCATE TABLE bg_weather_daily;

SET FOREIGN_KEY_CHECKS = 1;

