# Visual Crossing API Forecast Data Collection

A robust Python service for automatically fetching, storing, and maintaining weather forecast data from the Visual Crossing Weather API.

---

## Overview

This script creates and maintains a comprehensive local database of weather data for a specified location. It runs as a continuous service that fetches both current conditions and multi-day forecasts at configurable intervals, storing the data in a MySQL database for easy access by other applications.

---

## Features

- Real-time weather data collection from [Visual Crossing Weather API](https://www.visualcrossing.com/)
- Smart update scheduling with different intervals for current conditions and forecasts
- Complete weather data including:
  - **Current conditions**
  - **Daily forecasts** (7 days)
  - **Hourly forecasts**
  - **Weather alerts/warnings**
- Efficient database storage using upsert operations to avoid duplicates
- Comprehensive error handling and logging
- Configurable parameters for location and update frequency

---

## Requirements

- Python 3.6+
- MySQL Server

**Required Python packages:**
- [`requests`](https://pypi.org/project/requests/)
- [`mysql-connector-python`](https://pypi.org/project/mysql-connector-python/)
- [`schedule`](https://pypi.org/project/schedule/)

---

## Database Structure

The system creates and maintains four tables:

- `weather_current`: Real-time weather conditions
- `weather_daily`: Daily weather forecasts
- `weather_hourly`: Hourly weather forecasts
- `weather_alerts`: Weather warnings and alerts

---

## Configuration

Edit the following variables at the top of the script to customize the system:

```python
# API Configuration
API_KEY = 'YOUR_VISUAL_CROSSING_API_KEY'
LOCATION = 'Glasgow,UK'  # e.g., 'London,UK' or '37.8267,-122.4233'

# Database Configuration
DB_CONFIG = {
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'database': 'visual_crossing',
    'port': 3306
}

# Update intervals (in minutes)
CURRENT_UPDATE_INTERVAL = 5    # Update current conditions every 5 minutes
FORECAST_UPDATE_INTERVAL = 180 # Update forecast every 3 hours
FORECAST_DAYS = 7              # Number of days to forecast
```

---

## Installation

Clone this repository:

```bash
git clone https://github.com/yourusername/weather-forecast-system.git
cd weather-forecast-system
```

Install required packages:

```bash
pip install -r requirements.txt
```

Create a MySQL database:

```sql
CREATE DATABASE visual_crossing;
CREATE USER 'reporter'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON visual_crossing.* TO 'reporter'@'localhost';
FLUSH PRIVILEGES;
```

Update the configuration variables in the script with your API key and database credentials.

---

## Usage

Run the script to start the service:

```bash
python3 weather_updater.py
```

For production use, consider setting up a `systemd` service or using a process manager like Supervisor to ensure the script runs continuously and starts automatically on system boot.

---

## How It Works

1. The script initializes by creating the necessary database tables if they don't exist.
2. It immediately performs a full data update to populate the database.
3. It then starts two scheduled tasks:
    - A frequent update of current conditions (every 5 minutes by default)
    - A less frequent update of the full forecast (every 3 hours by default)
4. Each update fetches data from the Visual Crossing API and stores it in the database.
5. The system runs continuously, maintaining up-to-date weather information.

---

## Use Cases

- Power a weather dashboard or website
- Feed data to home automation systems
- Support IoT weather displays
- Enable weather-dependent scheduled tasks
- Analyze historical weather patterns
- Trigger alerts based on weather conditions

---

## Acknowledgments

Weather data provided by [Visual Crossing Weather API](https://www.visualcrossing.com/).

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
