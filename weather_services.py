#!/usr/bin/python3
import requests
import time
import threading
import yaml
import sys
import mysql.connector
from datetime import datetime
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("weather_station.log")
    ]
)
logger = logging.getLogger("WeatherStation")

# Global database connection and cursor
conn = None
cursor = None
db_lock = threading.Lock()  # Add lock for thread safety

# Database connection class with retry logic
class Database:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def connect(self):
        for attempt in range(self.max_retries):
            try:
                if self.connection is None or not self.connection.is_connected():
                    logger.info(f"Establishing new database connection (attempt {attempt+1}/{self.max_retries})")
                    self.connection = mysql.connector.connect(
                        host=self.config['host'],
                        user=self.config['user'],
                        password=self.config['password'],
                        database=self.config['database'],
                        connection_timeout=10,
                        autocommit=True  # Enable autocommit to avoid transaction issues
                    )
                return self.connection
            except mysql.connector.Error as err:
                logger.error(f"Database connection error (attempt {attempt+1}/{self.max_retries}): {err}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise

# Load configuration from file
def load_config():
    try:
        with open('weather_services_config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            if validate_config(config):
                return config
            else:
                logger.error("Configuration validation failed. Exiting.")
                sys.exit(1)
    except FileNotFoundError:
        logger.error("Configuration file 'weather_services_config.yaml' not found. Exiting.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {str(e)}. Exiting.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {str(e)}. Exiting.")
        sys.exit(1)

"""Validate the loaded configuration"""
def validate_config(config):
    # Check for services section
    if 'services' not in config:
        logger.error("Missing 'services' section in configuration file.")
        return False

    # Check for database section
    if 'database' not in config:
        logger.error("Missing 'database' section in configuration file.")
        return False

    # Validate database configuration
    db_config = config['database']
    required_db_fields = ['host', 'user', 'password', 'database']
    for field in required_db_fields:
        if field not in db_config:
            logger.error(f"Missing required database field: {field}")
            return False

    # List of required services
    required_services = ['weathercloud', 'wunderground', 'windy', 'pwsweather', 'metoffice']

    # Check each service
    for service in required_services:
        if service not in config['services']:
            logger.error(f"Missing service configuration: {service}")
            return False

        service_config = config['services'][service]

        # Check required fields for each service
        if 'enabled' not in service_config:
            logger.error(f"Missing 'enabled' field for service: {service}")
            return False

        if 'interval' not in service_config:
            logger.error(f"Missing 'interval' field for service: {service}")
            return False

        if 'credentials' not in service_config:
            logger.error(f"Missing 'credentials' field for service: {service}")
            return False

        # Check service-specific credential requirements
        creds = service_config['credentials']

        if service == 'weathercloud' and ('id' not in creds or 'key' not in creds or 'url' not in creds):
            logger.error(f"Missing required credentials for {service}")
            return False

        if service == 'wunderground' and ('id' not in creds or 'password' not in creds or 'url' not in creds):
            logger.error(f"Missing required credentials for {service}")
            return False

        # Modified Windy validation to only require the URL
        if service == 'windy' and 'url' not in creds:
            logger.error(f"Missing required credentials for {service}")
            return False

        if service == 'pwsweather' and ('id' not in creds or 'password' not in creds or 'url' not in creds or 'software' not in creds):
            logger.error(f"Missing required credentials for {service}")
            return False

        if service == 'metoffice' and ('siteid' not in creds or 'auth_key' not in creds or 'url' not in creds or 'software' not in creds):
            logger.error(f"Missing required credentials for {service}")
            return False

    return True

# Load configuration
logger.info("Loading configuration from weather_services_config.yaml")
CONFIG = load_config()
SERVICES = CONFIG['services']
DB_CONFIG = CONFIG['database']

# Conversion functions
def kmh_to_ms(speed_in_kmh):
    return speed_in_kmh * 0.277778 * 10

def mm_to_inches(rainfall_in_mm):
    return rainfall_in_mm * 0.0393701

def hpa_to_inches(pressure_in_hpa):
    return pressure_in_hpa * 0.02953

def degc_to_degf(temperature_in_c):
    return (temperature_in_c * (9 / 5.0)) + 32

def kmh_to_mph(speed_in_kmh):
    return float(speed_in_kmh) * 0.621371

# Initialize database connection
db = Database(DB_CONFIG)

# Central data retrieval function
def get_weather_data():
    global conn, cursor
    data = {}

    with db_lock:  # Use lock to ensure thread safety
        try:
            # Ensure the connection is active
            if conn is None or not conn.is_connected():
                logger.info("Connecting to database...")
                conn = db.connect()
                cursor = conn.cursor(buffered=True)  # Use buffered cursor

            logger.debug("Retrieving current weather data from database")

            # Temperature
            cursor.execute("SELECT AIR_TEMP FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No temperature data available")
                return None
            data['temperature'] = float(result[0])

            # Feels like temperature
            cursor.execute("SELECT FEELS_LIKE FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No feels_like data available")
                return None
            data['feels_like'] = float(result[0])

            # Sea level pressure
            cursor.execute("SELECT PRESSURE_SEA FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No pressure data available")
                return None
            data['pressure_sea'] = float(result[0])

            # Humidity
            cursor.execute("SELECT HUMIDITY FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No humidity data available")
                return None
            data['humidity'] = float(result[0])

            # Dew point
            cursor.execute("SELECT DEW_POINT FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No dew point data available")
                return None
            data['dew_point'] = float(result[0])

            # UV index
            cursor.execute("SELECT UV_INDEX FROM dataentry ORDER BY id DESC LIMIT 1;")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                logger.warning("No UV index data available")
                data['uv_index'] = 0.0  # Default to 0 if not available
            else:
                data['uv_index'] = float(result[0])

            # Wind direction (2 min avg)
            cursor.execute(
                "SELECT COALESCE(avg(WIND_DIRECTION),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -2 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind direction (2min) data available")
                data['wind_dir_2min'] = 0.0
            else:
                data['wind_dir_2min'] = float(result[0])

            # Wind speed (2 min avg)
            cursor.execute(
                "SELECT COALESCE(avg(WIND_SPEED),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -2 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind speed (2min) data available")
                data['wind_speed_2min'] = 0.0
            else:
                data['wind_speed_2min'] = float(result[0])

            # Wind speed (10 min avg)
            cursor.execute(
                "SELECT COALESCE(avg(WIND_SPEED),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -10 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind speed (10min) data available")
                data['wind_speed_10min'] = 0.0
            else:
                data['wind_speed_10min'] = float(result[0])

            # Wind gust (10 min max)
            cursor.execute(
                "SELECT COALESCE(max(WIND_GUST),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -10 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind gust (10min) data available")
                data['wind_gust_10min'] = 0.0
            else:
                data['wind_gust_10min'] = float(result[0])

            # Wind direction (10 min avg)
            cursor.execute(
                "SELECT COALESCE(avg(WIND_DIRECTION),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -10 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind direction (10min) data available")
                data['wind_dir_10min'] = 0.0
            else:
                data['wind_dir_10min'] = float(result[0])

            # Daily rainfall
            cursor.execute(
                "SELECT COALESCE(sum(RAINFALL),0) FROM dataentry WHERE CREATED BETWEEN curdate() AND now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No daily rainfall data available")
                data['daily_rain'] = 0.0
            else:
                data['daily_rain'] = float(result[0])

            # Hourly rainfall
            cursor.execute(
                "SELECT COALESCE(sum(RAINFALL),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -1 hour) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No hourly rainfall data available")
                data['hourly_rain'] = 0.0
            else:
                data['hourly_rain'] = float(result[0])

            # Wind speed (5 min avg) - for services that need it
            cursor.execute(
                "SELECT COALESCE(avg(WIND_SPEED),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -5 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind speed (5min) data available")
                data['wind_speed_5min'] = 0.0
            else:
                data['wind_speed_5min'] = float(result[0])

            # Wind gust (5 min max) - for services that need it
            cursor.execute(
                "SELECT COALESCE(max(WIND_GUST),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -5 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind gust (5min) data available")
                data['wind_gust_5min'] = 0.0
            else:
                data['wind_gust_5min'] = float(result[0])

            # Wind direction (5 min avg) - for services that need it
            cursor.execute(
                "SELECT COALESCE(avg(WIND_DIRECTION),0) FROM dataentry WHERE CREATED BETWEEN date_add(now(), interval -5 minute) and now();"
            )
            result = cursor.fetchone()
            if result is None:
                logger.warning("No wind direction (5min) data available")
                data['wind_dir_5min'] = 0.0
            else:
                data['wind_dir_5min'] = float(result[0])

            # Current timestamp
            data['timestamp'] = datetime.now()

            conn.commit()

            # Log summary of retrieved data
            logger.info(f"Retrieved weather data: Temp: {data['temperature']}°C, Pressure: {data['pressure_sea']} hPa, " +
                      f"Humidity: {data['humidity']}%, Wind: {data['wind_speed_10min']} km/h @ {data['wind_dir_10min']}°")

            return data

        except mysql.connector.Error as err:
            logger.error(f"Database error: {err}")
            # Try to reconnect
            try:
                if conn is not None and conn.is_connected():
                    conn.close()
            except:
                pass
            conn = None
            cursor = None
            return None

        except Exception as e:
            error_details = traceback.format_exc()  # Get detailed traceback
            logger.error(f"Unexpected error retrieving weather data: {str(e)}")
            logger.debug(f"Error details: {error_details}")
            return None

        finally:
            # Don't close the connection here, keep it open for reuse
            pass

# Service-specific submission functions
def submit_to_weathercloud(data):
    config = SERVICES['weathercloud']['credentials']

    logger.info("Preparing data for Weathercloud submission")

    # Format timestamp
    dt = int(data['timestamp'].timestamp())

    # Format temperature as int (C*10)
    temperature = int(data['temperature'] * 10)
    feels_like = int(data['feels_like'] * 10)

    # Format pressure as int (hPa*10)
    pressure = int(data['pressure_sea'] * 10)

    # Format humidity as int (0-100)
    humidity = int(data['humidity'])

    # Format wind data
    wind_speed = kmh_to_ms(data['wind_speed_10min'])  # m/s * 10
    wind_gust = kmh_to_ms(data['wind_gust_10min'])   # m/s * 10
    wind_dir = int(data['wind_dir_10min'])

    # Format rainfall in mm*10
    daily_rain = int(data['daily_rain'] * 10)

    # Format UV index
    uv_index = int(data['uv_index'] * 10)

    # Build parameters for Weathercloud
    params = {
        'wid': config['id'],
        'key': config['key'],
        'date': dt,
        'temp': temperature,
        'hum': humidity,
        'wdir': wind_dir,
        'wspd': int(wind_speed),
        'wgst': int(wind_gust),
        'bar': pressure,
        'rain': daily_rain,
        'uvi': uv_index,
        'tempf': feels_like
    }

    try:
        logger.debug(f"Sending request to Weathercloud with params: {params}")
        r = requests.get(config['url'], params=params, timeout=15)
        logger.info(f"Weathercloud update: {r.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if r.status_code != 200:
            logger.warning(f"Weathercloud returned non-200 status: {r.status_code}, response: {r.text}")
        else:
            logger.info(f"Successfully updated Weathercloud")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Weathercloud update failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Weathercloud: {str(e)}")
        return False

def submit_to_wunderground(data):
    config = SERVICES['wunderground']['credentials']

    logger.info("Preparing data for Weather Underground submission")

    # Format timestamp in ISO8601 format
    dt = data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

    # Convert temperature to Fahrenheit
    temp_f = round(degc_to_degf(data['temperature']), 1)

    # Convert pressure to inches
    pressure_in = round(hpa_to_inches(data['pressure_sea']), 2)

    # Convert rainfall to inches
    hourly_rain_in = round(mm_to_inches(data['hourly_rain']), 2)
    daily_rain_in = round(mm_to_inches(data['daily_rain']), 2)

    # Convert wind speed to mph
    wind_speed_mph = round(kmh_to_mph(data['wind_speed_2min']), 1)
    wind_gust_mph = round(kmh_to_mph(data['wind_gust_10min']), 1)

    # Get integer wind direction
    wind_dir = int(data['wind_dir_2min'])

    # Format humidity as integer
    humidity = int(data['humidity'])

    # Convert dew point to Fahrenheit
    dewpoint_f = round(degc_to_degf(data['dew_point']), 1)

    # Build API URL
    url = (
        config['url'] +
        "?ID=" + config['id'] +
        "&PASSWORD=" + config['password'] +
        "&dateutc=" + dt +
        "&tempf=" + str(temp_f) +
        "&baromin=" + str(pressure_in) +
        "&humidity=" + str(humidity) +
        "&dewptf=" + str(dewpoint_f) +
        "&windspeedmph=" + str(wind_speed_mph) +
        "&windgustmph=" + str(wind_gust_mph) +
        "&winddir=" + str(wind_dir) +
        "&rainin=" + str(hourly_rain_in) +
        "&dailyrainin=" + str(daily_rain_in) +
        "&action=updateraw"
    )

    try:
        # Hide password in debug logs
        masked_url = url.replace(config['password'], "PWD_HIDDEN")
        logger.debug(f"Sending request to Weather Underground: {masked_url}")

        r = requests.get(url, timeout=15)
        logger.info(f"Weather Underground update: {r.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if r.status_code != 200:
            logger.warning(f"Weather Underground returned non-200 status: {r.status_code}, response: {r.text}")
        else:
            logger.info(f"Successfully updated Weather Underground")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather Underground update failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Weather Underground: {str(e)}")
        return False

def submit_to_windy(data):
    config = SERVICES['windy']['credentials']

    logger.info("Preparing data for Windy submission")

    # Use the URL directly from configuration - this should include the JWT token
    # The URL should look like: "https://stations.windy.com/pws/update/eyJhbGc...?")
    if not config['url'].endswith('?'):
        base_url = config['url'] + '?'
    else:
        base_url = config['url']

    # Format timestamp in the format Windy expects (Y-m-d+H:M:S) if using dateutc param
    date = data['timestamp'].strftime("%Y-%m-%d")
    hours = data['timestamp'].strftime("%H")
    minutes = data['timestamp'].strftime("%M")
    seconds = data['timestamp'].strftime("%S")
    localdt = date + "+" + hours + ":" + minutes + ":" + seconds

    # Format values exactly as in your original script
    temperature_WI = "{:.1f}".format(data['temperature'])
    uv_index_WI = "{:.1f}".format(data['uv_index'])
    pressure_WI = "{:.1f}".format(data['pressure_sea'])
    humidity_WI = "{:.0f}".format(data['humidity'])
    dewpoint_WI = "{:.1f}".format(data['dew_point'])

    # For precipitation, use hourly rain
    precip_WI = "{:.2f}".format(data['hourly_rain'])

    # Convert wind speeds to mph as in your original script
    wind_speed_WI = "{:.1f}".format(kmh_to_mph(data['wind_speed_10min']))
    wind_gust_WI = "{:.1f}".format(kmh_to_mph(data['wind_gust_10min']))
    wind_direction_WI = "{:.0f}".format(data['wind_dir_10min'])

    # Build the URL with query parameters
    url = (
        base_url +
        "&temp=" + temperature_WI +
        "&uv=" + uv_index_WI +
        "&mbar=" + pressure_WI +
        "&rh=" + humidity_WI +
        "&dewpoint=" + dewpoint_WI +
        "&precip=" + precip_WI +
        "&windspeedmph=" + wind_speed_WI +
        "&windgustmph=" + wind_gust_WI +
        "&winddir=" + wind_direction_WI
    )

    try:
        logger.debug(f"Sending request to Windy with URL: {url}")
        r = requests.get(url, timeout=15)
        logger.info(f"Windy update: {r.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if r.status_code != 200:
            logger.warning(f"Windy returned non-200 status: {r.status_code}, response: {r.text}")
        else:
            logger.info(f"Successfully updated Windy")

        # For debugging
        logger.debug(f"Windy request URL: {r.request.url}")

        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Windy update failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Windy: {str(e)}")
        return False

def submit_to_pwsweather(data):
    config = SERVICES['pwsweather']['credentials']

    logger.info("Preparing data for PWSWeather submission")

    # Format timestamp in ISO8601 format
    dt = data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

    # Convert temperature to Fahrenheit
    temp_f = round(degc_to_degf(data['temperature']), 1)

    # Convert pressure to inches
    pressure_in = round(hpa_to_inches(data['pressure_sea']), 2)

    # Convert rainfall to inches
    hourly_rain_in = round(mm_to_inches(data['hourly_rain']), 2)
    daily_rain_in = round(mm_to_inches(data['daily_rain']), 2)

    # Convert wind speed to mph
    wind_speed_mph = round(kmh_to_mph(data['wind_speed_2min']), 1)
    wind_gust_mph = round(kmh_to_mph(data['wind_gust_10min']), 1)

    # Get integer wind direction
    wind_dir = int(data['wind_dir_2min'])

    # Format humidity as integer
    humidity = int(data['humidity'])

    # Convert dew point to Fahrenheit
    dewpoint_f = round(degc_to_degf(data['dew_point']), 1)

    # Build parameters for GET request
    params = {
        "ID": config['id'],
        "PASSWORD": config['password'],
        "dateutc": dt,
        "tempf": temp_f,
        "humidity": humidity,
        "dewptf": dewpoint_f,
        "baromin": pressure_in,
        "windspeedmph": wind_speed_mph,
        "windgustmph": wind_gust_mph,
        "winddir": wind_dir,
        "rainin": hourly_rain_in,
        "dailyrainin": daily_rain_in,
        "softwaretype": config['software'],
        "action": "updateraw"
    }

    try:
        # Hide password in debug logs
        debug_params = params.copy()
        debug_params['PASSWORD'] = 'PWD_HIDDEN'
        logger.debug(f"Sending request to PWSWeather: {debug_params}")

        r = requests.get(config['url'], params=params, timeout=15)
        logger.info(f"PWSWeather update: {r.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if r.status_code != 200:
            logger.warning(f"PWSWeather returned non-200 status: {r.status_code}, response: {r.text}")
        else:
            logger.info(f"Successfully updated PWSWeather")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"PWSWeather update failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating PWSWeather: {str(e)}")
        return False

def submit_to_metoffice(data):
    config = SERVICES['metoffice']['credentials']

    logger.info("Preparing data for Met Office submission")

    # Format timestamp
    dt = data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

    # Format temperature (°C)
    temperature = round(data['temperature'], 1)

    # Format dew point (°C)
    dew_point = round(data['dew_point'], 1)

    # Format pressure (hPa)
    pressure = round(data['pressure_sea'], 1)

    # Format humidity (%)
    humidity = int(data['humidity'])

    # Format wind data
    wind_dir = int(data['wind_dir_10min'])
    wind_speed_kmh = round(data['wind_speed_10min'], 1)  # km/h
    wind_gust_kmh = round(data['wind_gust_10min'], 1)    # km/h

    # Format rainfall (mm)
    hourly_rain = round(data['hourly_rain'], 1)

    # Format UV index
    uv_index = round(data['uv_index'], 1)

    # Format parameters for Met Office
    params = {
        "siteid": config['siteid'],
        "siteAuthenticationKey": config['auth_key'],
        "dateutc": dt,
        "tempf": round(degc_to_degf(temperature), 1),  # Met Office wants Fahrenheit
        "humidity": humidity,
        "dewptf": round(degc_to_degf(dew_point), 1),  # Met Office wants Fahrenheit
        "baromin": round(hpa_to_inches(pressure), 2),  # Met Office wants inches
        "windspeedmph": round(kmh_to_mph(wind_speed_kmh), 1),  # Met Office wants mph
        "windgustmph": round(kmh_to_mph(wind_gust_kmh), 1),  # Met Office wants mph
        "winddir": wind_dir,
        "rainin": round(mm_to_inches(hourly_rain), 2),  # Met Office wants inches
        "UV": uv_index,
        "softwaretype": config['software']
    }

    try:
        # Hide auth key in debug logs
        debug_params = params.copy()
        debug_params['siteAuthenticationKey'] = 'AUTH_KEY_HIDDEN'
        logger.debug(f"Sending request to Met Office: {debug_params}")

        r = requests.get(config['url'], params=params, timeout=15)
        logger.info(f"Met Office update: {r.status_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if r.status_code != 200:
            logger.warning(f"Met Office returned non-200 status: {r.status_code}, response: {r.text}")
        else:
            logger.info(f"Successfully updated Met Office")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Met Office update failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Met Office: {str(e)}")
        return False

# Service runner
def service_runner(service_name, interval):
    """Run the service in a loop with specified interval"""
    logger.info(f"Starting {service_name} service runner with {interval} second interval")

    # Dictionary mapping service names to their submission functions
    service_functions = {
        'weathercloud': submit_to_weathercloud,
        'wunderground': submit_to_wunderground,
        'windy': submit_to_windy,
        'pwsweather': submit_to_pwsweather,
        'metoffice': submit_to_metoffice
    }

    # Get the submission function for this service
    submit_func = service_functions[service_name]

    # Run the service loop
    next_run = 0  # Run immediately on first iteration

    while True:
        try:
            # Sleep until next scheduled run
            sleep_time = max(0, next_run - time.time())
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Log the service activity
            logger.info(f"[{service_name}] Retrieving weather data")

            # Get the weather data
            data = get_weather_data()

            if data is None:
                logger.warning(f"[{service_name}] No weather data available for update")
            else:
                # Submit data to the service
                submit_func(data)

            # Calculate next run time
            next_run = time.time() + interval

            # Log next scheduled update time
            next_update_time = datetime.fromtimestamp(next_run).strftime("%H:%M:%S")
            logger.info(f"[{service_name}] Next update in {interval} seconds at {next_update_time}")

        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Error in {service_name} service: {str(e)}")
            logger.debug(f"Error details: {error_details}")

            # Don't bombard the service if there's an error - wait before retrying
            time.sleep(min(interval, 30))  # Wait at least 30 seconds

            # Recalculate next run time
            next_run = time.time() + interval

def init_service(service_name):
    """Initialize a service from the configuration"""
    if service_name not in SERVICES:
        logger.error(f"Service {service_name} not found in configuration")
        return False

    service_config = SERVICES[service_name]

    # Check if the service is enabled
    if not service_config.get('enabled', False):
        logger.info(f"Service {service_name} is disabled in configuration")
        return False

    # Get the service interval
    interval = int(service_config.get('interval', 300))  # Default to 300 seconds (5 minutes)
    logger.info(f"Initializing {service_name} service with {interval} second interval")

    # Create and start the service thread
    thread = threading.Thread(
        target=service_runner,
        args=(service_name, interval),
        name=f"{service_name}_thread",
        daemon=True  # Allow the program to exit even if the thread is running
    )
    thread.start()
    logger.info(f"Started {service_name} service thread")

    return thread

def main():
    """Main function to initialize and run all services"""
    logger.info("=== Weather Station Service Starting ===")

    # Initialize database connection
    try:
        global conn, cursor
        logger.info("Establishing new database connection")
        conn = db.connect()
        cursor = conn.cursor()
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        sys.exit(1)

    # List of services to initialize
    services = ['weathercloud', 'wunderground', 'windy', 'pwsweather', 'metoffice']

    # Initialize each service and keep track of the threads
    threads = {}

    for service_name in services:
        thread = init_service(service_name)
        if thread:
            threads[service_name] = thread

    logger.info("=== Weather Station Service Running ===")

    # Periodically check that all services are still running
    while True:
        try:
            # List active services
            active_services = [name for name, thread in threads.items() if thread.is_alive()]
            logger.info(f"Service status: {len(active_services)}/{len(threads)} active ({', '.join(active_services)})")

            # If any service has died, restart it
            for service_name, thread in list(threads.items()):
                if not thread.is_alive():
                    logger.warning(f"Service {service_name} has stopped. Restarting...")
                    new_thread = init_service(service_name)
                    if new_thread:
                        threads[service_name] = new_thread

            # Sleep for a minute before checking again
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal. Exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
