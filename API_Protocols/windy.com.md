
# Personal Weather Station Upload Protocol

Windy.com supports two ways to upload data from your Personal Weather Station (PWS):

---

## **A. GET Parameters**

- **URL:**  
  `https://stations.windy.com/pws/update/API-KEY`
- **Purpose:** Update a single station's info and measurements using URL parameters.

**Example:**

```
https://stations.windy.com/pws/update/XXX-API-KEY-XXX?winddir=230&windspeedmph=12&windgustmph=12&tempf=70&rainin=0&baromin=29.1&dewptf=68.2&humidity=90
```

---

## **B. POST JSON**

- **URL:**  
  `https://stations.windy.com/pws/update/API-KEY`
- **Purpose:** Upload data for one or more stations in a single call (useful for bulk or frequent uploads).
- **Payload:** JSON

**Example JSON:**

```json
{
  "stations": [
    { "station": 0, "name": "My Home Station", "lat": 48.2, "lon": 28.6, "elevation": 80, "tempheight": 2, "windheight": 10 },
    { "station": 1, "name": "My Other Station", "lat": 47.1, "lon": 31.2, "elevation": 122, "tempheight": 2, "windheight": 8 }
  ],
  "observations": [
    { "station": 0, "dateutc": "2019-03-15T06:15:34", "temp": 1.2, "wind": 2.8, "winddir": 189, "gust": 3.7, "rh": 76 },
    { "station": 1, "dateutc": "2019-03-15T06:15:34", "temp": 2.6, "wind": 1.1, "winddir": 135, "gust": 2.5, "rh": 65 }
  ]
}
```

---

## **Parameters**

### **URL Parameter**

- **API Key:**  
  *text, required* – API key generated for each registered user at PWS web API

---

### **Station Info Parameters (used under `stations`)**

| Name        | Type      | Description                                                    | Alternatives  | Required |
|-------------|-----------|----------------------------------------------------------------|---------------|----------|
| station     | integer   | Station ID (32 bit integer); for multiple stations, default 0  | si, stationId | Yes      |
| shareOption | text      | Data sharing: `Open`, `Only Windy`, `Private` (default: Open)  | —             | No       |
| name        | text      | User-selected station name                                     | —             | No       |
| lat         | number    | Latitude (degrees)                                             | latitude      | Yes      |
| lon         | number    | Longitude (degrees)                                            | longitude     | Yes      |
| elevation   | number    | Height above sea level (meters)                                | elev, elev_m, altitude | No|
| tempheight  | number    | Temperature sensor height (meters)                             | agl_temp      | No       |
| windheight  | number    | Wind sensor height (meters)                                    | agl_wind      | No       |

*Station record is created in the database as soon as required info params are uploaded.*

---

### **Measurement Parameters (used under `observations`)**

| Name           | Type         | Description                                                     | Alternatives            | Unit     |
|----------------|--------------|-----------------------------------------------------------------|-------------------------|----------|
| station        | integer      | Station ID (see above); default 0                               | si, stationId           | —        |
| time           | text         | ISO string time: `"YYYY-MM-DDTHH:MM:SS.sssZ"`                   | —                       | —        |
| dateutc        | text         | UTC time: `"YYYY-MM-DD HH:MM:SS"`                               | —                       | —        |
| ts             | integer      | UNIX timestamp (seconds or ms)                                  | —                       | —        |
| temp           | number       | Air temperature                                                 | tempf                   | °C/°F    |
| wind           | number       | Wind speed                                                      | windspeedmph            | m/s, mph |
| winddir        | integer      | Instantaneous wind direction                                    | —                       | degrees  |
| gust           | number       | Current wind gust                                               | windgustmph             | m/s, mph |
| rh             | number       | Relative humidity                                               | humidity                | %        |
| dewpoint       | number       | Dew point                                                       | —                       | °C       |
| pressure       | number       | Atmospheric pressure                                            | mbar, baromin           | Pa, hPa, inHg |
| precip         | number       | Precipitation over past hour                                    | rainin                  | mm, in   |
| uv             | number       | UV Index                                                        | —                       | index    |

**Note:** All fields must be URL-escaped in GET requests.

---

## **Additional Notes**

- `station`, `lat`, and `lon` are the minimum info required to create a station.
- For alternative field names and units, refer to Windy.com [docs](https://community.windy.com/topic/8168/report-your-weather-station-data-to-windy).
- Always URL-escape parameters in the GET protocol.

---

**References:**
- [Windy.com PWS Protocol](https://community.windy.com/topic/8168/report-your-weather-station-data-to-windy)
