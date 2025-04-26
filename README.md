# Weather Station Service
A robust multi-service weather station data submission system designed to collect and report weather data from your personal weather station to popular weather platforms.

# Overview
This project enables automatic submission of weather data from your personal weather station to multiple weather services including:

- Weather Underground
- Weathercloud
- Windy
- PWS Weather
- Met Office (UK Weather Observations Website)
  
The service collects data from a MySQL database containing weather measurements and submits them to configured services at regular intervals. It features robust error handling, connection management, and automatic recovery from network or service failures.

# Features
- Multi-Service Support: Submit to 5 popular weather platforms simultaneously
- Configurable Intervals: Set different update intervals for each service
- Robust Error Handling: Automatic recovery from network or service failures
- Database Integration: Works with a standard MySQL/MariaDB database schema
- Detailed Logging: Comprehensive logging for monitoring and troubleshooting
- Resource Efficient: Designed to run on low-power devices like Raspberry Pi

# Requirements
Python 3.6 or higher
MySQL/MariaDB database
Weather station hardware collecting data into the MySQL database

# Dependencies
`pip install mysql-connector-python requests pyyaml`

# Set up Database
`mysql -u your_mysql_user -p < weather_db_template.sql`

# Configure the service
Copy the example configuration file and edit it with your credentials:

`cp weather_services_config_template.yaml weather_services_config.yaml`  
`vi weather_services_config.yaml`

### Update the configuration with your:

Database credentials
Weather service API keys/tokens
Desired update intervals

# Database Structure
The service expects a MySQL database with the following structure:

```sql
CREATE TABLE `dataentry` (  
  `ID` bigint(20) NOT NULL AUTO_INCREMENT,  
  `CREATED` timestamp NOT NULL DEFAULT current_timestamp(),  
  `HUMIDITY` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT '0-100 % RH',  
  `AIR_TEMP` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'Celcius',  
  `FEELS_LIKE` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'Celsius',  
  `DEW_POINT` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'Celsius',  
  `PRESSURE_SEA` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'hPa',  
  `RAINFALL` decimal(6,2) NOT NULL DEFAULT 0.00 COMMENT 'Millimeters',  
  `WIND_SPEED` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'KPH',  
  `WIND_GUST` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'KPH',  
  `WIND_DIRECTION` int(3) NOT NULL DEFAULT 0 COMMENT 'Degrees',  
  `WIND_CARDINAL` varchar(3) NOT NULL DEFAULT '0' COMMENT 'Wind Cardinal',  
  `UV_INDEX` decimal(6,1) NOT NULL COMMENT 'UV Exposure Index',  
  `TEMP_CASE` decimal(6,1) NOT NULL DEFAULT 0.0 COMMENT 'Celcius',  
  PRIMARY KEY (`ID`)  
);
```
# Running the Service
Manual start
`python weather_station_service.py`

# Troubleshooting
Common Issues
1. Database Connection Errors
- Check your database credentials
- Ensure MySQL service is running
- Verify network connectivity if using a remote database

2. API Submission Failures
- Verify API credentials for each service
- Check internet connectivity
- Confirm data format matches service requirements

3.Service Not Starting
- Check logs for detailed error messages
- Verify Python dependencies are installed
- Ensure configuration file is properly formatted

# Acknowledgments
Thanks to Weather Underground, Weathercloud, Windy, PWS Weather, and Met Office for providing APIs for personal weather stations
Inspired by various weather station projects in the Raspberry Pi community and around the wild west
