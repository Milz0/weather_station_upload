#!/usr/bin/python3
import requests
import mysql.connector
import time
import schedule
from datetime import datetime, timedelta
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("weather_updater.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("weather_updater")

# Configuration
API_KEY = ''
LOCATION = ''  # e.g., 'London,UK' or '37.8267,-122.4233'
DB_CONFIG = {
    'user': '',
    'password': '',
    'host': 'localhost',
    'database': '',
    'port': 3306
}

# Update intervals (in minutes)
CURRENT_UPDATE_INTERVAL = 5  # Update current conditions every 15 minutes
FORECAST_UPDATE_INTERVAL = 180  # Update forecast every 6 hours (360 minutes)
FORECAST_DAYS = 7  # Number of days to forecast

# API parameters
API_PARAMS = {
    'unitGroup': 'metric',  # Options: us, metric, uk
    'include': 'days,hours,current,alerts',
    'contentType': 'json',
    'key': API_KEY
}

# API parameters for current conditions only (to reduce data usage)
CURRENT_API_PARAMS = {
    'unitGroup': 'metric',
    'include': 'current',
    'contentType': 'json',
    'key': API_KEY
}

def create_database_tables():
    """Create the necessary database tables if they don't exist."""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        # Create table for daily forecasts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_daily (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                temp FLOAT,
                temp_min FLOAT,
                temp_max FLOAT,
                feelslike FLOAT,
                humidity FLOAT,
                dew FLOAT,
                precip FLOAT,
                precipprob FLOAT,
                precipcover FLOAT,
                preciptype VARCHAR(50),
                snow FLOAT,
                snowdepth FLOAT,
                windgust FLOAT,
                windspeed FLOAT,
                winddir FLOAT,
                pressure FLOAT,
                cloudcover FLOAT,
                visibility FLOAT,
                solarradiation FLOAT,
                solarenergy FLOAT,
                uvindex FLOAT,
                sunrise VARCHAR(10),
                sunset VARCHAR(10),
                moonphase FLOAT,
                conditions VARCHAR(255),
                description VARCHAR(500),
                icon VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY location_date (location, date)
            )
        ''')

        # Create table for hourly forecasts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_hourly (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                datetime DATETIME NOT NULL,
                temp FLOAT,
                feelslike FLOAT,
                humidity FLOAT,
                dew FLOAT,
                precip FLOAT,
                precipprob FLOAT,
                preciptype VARCHAR(50),
                snow FLOAT,
                snowdepth FLOAT,
                windgust FLOAT,
                windspeed FLOAT,
                winddir FLOAT,
                pressure FLOAT,
                cloudcover FLOAT,
                visibility FLOAT,
                solarradiation FLOAT,
                solarenergy FLOAT,
                uvindex FLOAT,
                conditions VARCHAR(255),
                icon VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY location_datetime (location, datetime)
            )
        ''')

        # Create table for current conditions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_current (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                datetime DATETIME NOT NULL,
                temp FLOAT,
                feelslike FLOAT,
                humidity FLOAT,
                dew FLOAT,
                precip FLOAT,
                preciptype VARCHAR(50),
                snow FLOAT,
                snowdepth FLOAT,
                windgust FLOAT,
                windspeed FLOAT,
                winddir FLOAT,
                pressure FLOAT,
                cloudcover FLOAT,
                visibility FLOAT,
                solarradiation FLOAT,
                solarenergy FLOAT,
                uvindex FLOAT,
                conditions VARCHAR(255),
                icon VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY location_key (location)
            )
        ''')

        # Create table for weather alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                alert_id VARCHAR(100) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                severity VARCHAR(50),
                event VARCHAR(100),
                onset DATETIME,
                ends DATETIME,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY alert_key (location, alert_id)
            )
        ''')

        connection.commit()
        logger.info("Database tables created or already exist")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    finally:
        cursor.close()
        connection.close()

def get_weather_forecast(current_only=False):
    """Retrieve weather forecast data from Visual Crossing API.

    Args:
        current_only (bool): If True, only fetch current conditions to save API credits
    """
    base_url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{LOCATION}'

    # Use different parameters based on what we're fetching
    params = CURRENT_API_PARAMS if current_only else API_PARAMS

    if not current_only:
        # For full forecast, specify date range
        today = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=FORECAST_DAYS)).strftime('%Y-%m-%d')
        url = f'{base_url}/{today}/{end_date}'
    else:
        # For current conditions only, no date range needed
        url = base_url

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            logger.info(f"Successfully retrieved weather data for {LOCATION} ({'current only' if current_only else 'full forecast'})")
            return response.json()
        else:
            logger.error(f"Error fetching data: HTTP {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception while fetching weather data: {e}")
        return None

def update_daily_forecast(connection, data, location):
    """Update daily forecast data in the database."""
    cursor = connection.cursor()

    try:
        for day in data.get('days', []):
            # Extract values with defaults for missing data
            values = {
                'location': location,
                'date': day.get('datetime'),
                'temp': day.get('temp'),
                'temp_min': day.get('tempmin'),
                'temp_max': day.get('tempmax'),
                'feelslike': day.get('feelslike'),
                'humidity': day.get('humidity'),
                'dew': day.get('dew'),
                'precip': day.get('precip'),
                'precipprob': day.get('precipprob'),
                'precipcover': day.get('precipcover'),
                'preciptype': ','.join(day.get('preciptype', [])) if day.get('preciptype') else None,
                'snow': day.get('snow'),
                'snowdepth': day.get('snowdepth'),
                'windgust': day.get('windgust'),
                'windspeed': day.get('windspeed'),
                'winddir': day.get('winddir'),
                'pressure': day.get('pressure'),
                'cloudcover': day.get('cloudcover'),
                'visibility': day.get('visibility'),
                'solarradiation': day.get('solarradiation'),
                'solarenergy': day.get('solarenergy'),
                'uvindex': day.get('uvindex'),
                'sunrise': day.get('sunrise'),
                'sunset': day.get('sunset'),
                'moonphase': day.get('moonphase'),
                'conditions': day.get('conditions'),
                'description': day.get('description'),
                'icon': day.get('icon')
            }

            # Create placeholders and values for SQL query
            placeholders = ', '.join(['%s'] * len(values))
            columns = ', '.join(values.keys())
            update_stmt = ', '.join([f"{k} = VALUES({k})" for k in values.keys()])

            # Prepare SQL query
            query = f'''
                INSERT INTO weather_daily ({columns})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_stmt}, last_updated = CURRENT_TIMESTAMP
            '''

            cursor.execute(query, list(values.values()))

        connection.commit()
        logger.info(f"Updated daily forecast data for {location}")
    except Exception as e:
        logger.error(f"Error updating daily forecast: {e}")
        connection.rollback()
    finally:
        cursor.close()

def update_hourly_forecast(connection, data, location):
    """Update hourly forecast data in the database."""
    cursor = connection.cursor()

    try:
        for day in data.get('days', []):
            date = day.get('datetime')

            for hour in day.get('hours', []):
                # Create datetime from date and hour
                hour_time = hour.get('datetime', '00:00:00')
                datetime_str = f"{date} {hour_time}"

                values = {
                    'location': location,
                    'date': date,
                    'datetime': datetime_str,
                    'temp': hour.get('temp'),
                    'feelslike': hour.get('feelslike'),
                    'humidity': hour.get('humidity'),
                    'dew': hour.get('dew'),
                    'precip': hour.get('precip'),
                    'precipprob': hour.get('precipprob'),
                    'preciptype': ','.join(hour.get('preciptype', [])) if hour.get('preciptype') else None,
                    'snow': hour.get('snow'),
                    'snowdepth': hour.get('snowdepth'),
                    'windgust': hour.get('windgust'),
                    'windspeed': hour.get('windspeed'),
                    'winddir': hour.get('winddir'),
                    'pressure': hour.get('pressure'),
                    'cloudcover': hour.get('cloudcover'),
                    'visibility': hour.get('visibility'),
                    'solarradiation': hour.get('solarradiation'),
                    'solarenergy': hour.get('solarenergy'),
                    'uvindex': hour.get('uvindex'),
                    'conditions': hour.get('conditions'),
                    'icon': hour.get('icon')
                }

                # Create placeholders and values for SQL query
                placeholders = ', '.join(['%s'] * len(values))
                columns = ', '.join(values.keys())
                update_stmt = ', '.join([f"{k} = VALUES({k})" for k in values.keys()])

                # Prepare SQL query
                query = f'''
                    INSERT INTO weather_hourly ({columns})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_stmt}, last_updated = CURRENT_TIMESTAMP
                '''

                cursor.execute(query, list(values.values()))

        connection.commit()
        logger.info(f"Updated hourly forecast data for {location}")
    except Exception as e:
        logger.error(f"Error updating hourly forecast: {e}")
        connection.rollback()
    finally:
        cursor.close()

def update_current_conditions(connection, data, location):
    """Update current weather conditions in the database."""
    cursor = connection.cursor()

    try:
        current = data.get('currentConditions', {})
        if current:
            # Get current datetime
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            values = {
                'location': location,
                'datetime': current_datetime,
                'temp': current.get('temp'),
                'feelslike': current.get('feelslike'),
                'humidity': current.get('humidity'),
                'dew': current.get('dew'),
                'precip': current.get('precip'),
                'preciptype': ','.join(current.get('preciptype', [])) if current.get('preciptype') else None,
                'snow': current.get('snow'),
                'snowdepth': current.get('snowdepth'),
                'windgust': current.get('windgust'),
                'windspeed': current.get('windspeed'),
                'winddir': current.get('winddir'),
                'pressure': current.get('pressure'),
                'cloudcover': current.get('cloudcover'),
                'visibility': current.get('visibility'),
                'solarradiation': current.get('solarradiation'),
                'solarenergy': current.get('solarenergy'),
                'uvindex': current.get('uvindex'),
                'conditions': current.get('conditions'),
                'icon': current.get('icon')
            }

            # Create placeholders and values for SQL query
            placeholders = ', '.join(['%s'] * len(values))
            columns = ', '.join(values.keys())
            update_stmt = ', '.join([f"{k} = VALUES({k})" for k in values.keys()])

            # Prepare SQL query
            query = f'''
                INSERT INTO weather_current ({columns})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_stmt}, last_updated = CURRENT_TIMESTAMP
            '''

            cursor.execute(query, list(values.values()))

            connection.commit()
            logger.info(f"Updated current conditions for {location}")
    except Exception as e:
        logger.error(f"Error updating current conditions: {e}")
        connection.rollback()
    finally:
        cursor.close()

def update_weather_alerts(connection, data, location):
    """Update weather alerts in the database."""
    cursor = connection.cursor()

    try:
        alerts = data.get('alerts', [])
        if alerts:
            for alert in alerts:
                values = {
                    'location': location,
                    'alert_id': alert.get('id', ''),
                    'title': alert.get('title', ''),
                    'description': alert.get('description', ''),
                    'severity': alert.get('severity', ''),
                    'event': alert.get('event', ''),
                    'onset': alert.get('onset', ''),
                    'ends': alert.get('ends', '')
                }

                # Create placeholders and values for SQL query
                placeholders = ', '.join(['%s'] * len(values))
                columns = ', '.join(values.keys())
                update_stmt = ', '.join([f"{k} = VALUES({k})" for k in values.keys()])

                # Prepare SQL query
                query = f'''
                    INSERT INTO weather_alerts ({columns})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_stmt}, last_updated = CURRENT_TIMESTAMP
                '''

                cursor.execute(query, list(values.values()))

            connection.commit()
            logger.info(f"Updated weather alerts for {location}")
    except Exception as e:
        logger.error(f"Error updating weather alerts: {e}")
        connection.rollback()
    finally:
        cursor.close()

def update_current_only():
    """Update only the current weather conditions."""
    logger.info("Starting current conditions update...")

    try:
        # Get only current weather data from API
        weather_data = get_weather_forecast(current_only=True)

        if not weather_data:
            logger.error("Failed to retrieve current weather data. Skipping update.")
            return

        # Get location name from the response
        location = weather_data.get('address', LOCATION)

        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)

        # Update current conditions only
        update_current_conditions(connection, weather_data, location)

        # Close database connection
        connection.close()

        logger.info("Current conditions update completed successfully")
    except mysql.connector.Error as err:
        logger.error(f"Database error during current update: {err}")
    except Exception as e:
        logger.error(f"Unexpected error during current update: {e}")

def update_full_forecast():
    """Update all weather data including forecast."""
    logger.info("Starting full weather data update...")

    try:
        # Get complete weather data from API
        weather_data = get_weather_forecast(current_only=False)

        if not weather_data:
            logger.error("Failed to retrieve weather data. Skipping database update.")
            return

        # Get location name from the response
        location = weather_data.get('address', LOCATION)

        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)

        # Update all data types
        update_daily_forecast(connection, weather_data, location)
        update_hourly_forecast(connection, weather_data, location)
        update_current_conditions(connection, weather_data, location)
        update_weather_alerts(connection, weather_data, location)

        # Close database connection
        connection.close()

        logger.info("Full weather data update completed successfully")
    except mysql.connector.Error as err:
        logger.error(f"Database error during full update: {err}")
    except Exception as e:
        logger.error(f"Unexpected error during full update: {e}")

def start_scheduler():
    """Set up and start the scheduler with different intervals."""
    # Schedule current conditions update every CURRENT_UPDATE_INTERVAL minutes
    schedule.every(CURRENT_UPDATE_INTERVAL).minutes.do(update_current_only)

    # Schedule full forecast update every FORECAST_UPDATE_INTERVAL minutes
    schedule.every(FORECAST_UPDATE_INTERVAL).minutes.do(update_full_forecast)

    # Run full update immediately on startup
    update_full_forecast()

    logger.info(f"Scheduler started: Current conditions every {CURRENT_UPDATE_INTERVAL} minutes, "
                f"Full forecast every {FORECAST_UPDATE_INTERVAL} minutes")

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check for pending tasks every 30 seconds

def run_as_service():
    """Run the application as a service with proper initialization."""
    try:
        # Create database tables if they don't exist
        create_database_tables()

        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

        # Keep the main thread alive
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    run_as_service()
