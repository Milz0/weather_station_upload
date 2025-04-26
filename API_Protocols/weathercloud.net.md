
# Weathercloud API Documentation

---

## URL Formats

1. 
   ```
   http://api.weathercloud.net/v01/set/wid/$WID/key/$Key/...<parameters>…
   ```
2.
   ```
   http://api.weathercloud.net/v01/set?wid=$WID&key=$Key&…<parameters>…
   ```

## User Verification

- Requests must contain only `WID` and `Key`.

## Timing

- **Data interval:** 10 minutes.
- **Pro and Premium users:** 1 minute.
- Requests faster than the allowed interval will be **rejected**.

## Return Codes

- `200` – Success
- `400` – Bad request
- `401` – Incorrect WID or Key
- `429` – Too many requests
- `500` – Unexpected server error

---

## Parameters

### Temperature

| Parameter                          | Range   | Example      |
|-------------------------------------|---------|--------------|
| `temp`, `tempin`, `temp02`, `tempagro`, `chill`, `dew`, `dewin`, `heat`, `heatin` | ºC x 10 [-400, 600] | 20.5 ºC → `205` |

### Humidity

| Parameter         | Range | Example     |
|-------------------|-------|-------------|
| `hum`, `humin`, `hum02` | % [0, 100] | 40 % → `40` |

### Atmospheric Pressure

| Parameter | Range | Example      |
|-----------|-------|--------------|
| `bar`     | hPa x 10 [9000, 11000] | 1013.0 hPa → `10130` |

### Wind Speed

| Parameter                   | Range           | Example          |
|-----------------------------|-----------------|------------------|
| `wspd`, `wspdavg`, `wspdhi` | m/s x 10 [0,600]| 12.5 m/s → `125` |

### Wind Direction

| Parameter                         | Range         | Example          |
|------------------------------------|--------------|------------------|
| `wdir`, `wdiravg`, `wdirhi`        | º [0,359]    | 180 º → `180`    |

### Rain (Daily Total)

| Parameter | Range              | Example         |
|-----------|-------------------|-----------------|
| `rain`    | mm x 10 [0,10000] | 35.0 mm → `350` |

### Rain Rate

| Parameter | Range               | Example         |
|-----------|--------------------|-----------------|
| `rainrate`| mm/h x 10 [0,1000] | 20.0 mm/h → `200`|

### ET (Daily Total)

| Parameter | Range             | Example         |
|-----------|------------------|-----------------|
| `et`      | mm x 10 [0,1000] | 7.5 mm → `75`   |

### Solar Radiation

| Parameter   | Range                      | Example            |
|-------------|---------------------------|--------------------|
| `solarrad`  | W/m² x 10 [0,20000]        | 1050 W/m² → `10500`|

### UV Index

| Parameter | Range     | Example     |
|-----------|-----------|-------------|
| `uvi`     | x 10 [0,160] | 8.0 → `80`  |

### Soil Moisture

| Parameter   | Range        | Example          |
|-------------|--------------|------------------|
| `soilmoist` | Cb [0,200]   | 100 cb → `100`   |

### Leaf Wetness

| Parameter   | Range        | Example         |
|-------------|--------------|-----------------|
| `leafwet`   | [0,15]       | 10 → `10`       |

### Air Quality Index (US AQI)

| Parameter | Range      | Example        |
|-----------|------------|----------------|
| `aqi`     | [0,500]    | 100 → `100`    |

### PM2.5

| Parameter | Range               | Example               |
|-----------|---------------------|-----------------------|
| `pm25`    | μg/m³ [0,2000]      | 150 μg/m³ → `150`     |

### PM10

| Parameter | Range                | Example               |
|-----------|----------------------|-----------------------|
| `pm10`    | μg/m³ [0,5000]       | 150 μg/m³ → `150`     |

### CO

| Parameter | Range             | Example         |
|-----------|------------------|-----------------|
| `co`      | ppb [0,10000]    | 750 ppb → `750` |

### NO

| Parameter | Range           | Example          |
|-----------|----------------|------------------|
| `no`      | ppb [0,2000]   | 250 ppb → `250`  |

### NO2

| Parameter | Range           | Example          |
|-----------|----------------|------------------|
| `no2`     | ppb [0,2000]   | 250 ppb → `250`  |

### SO2

| Parameter | Range           | Example          |
|-----------|----------------|------------------|
| `so2`     | ppb [0,2000]   | 250 ppb → `250`  |

### O3

| Parameter | Range           | Example          |
|-----------|----------------|------------------|
| `o3`      | ppb [0,2000]   | 250 ppb → `250`  |

### Noise

| Parameter | Range             | Example         |
|-----------|------------------|-----------------|
| `noise`   | dB x 10 [0,1200] | 60.0 dB → `600` |

### Power Supply

| Parameter | Range           | Example         |
|-----------|----------------|-----------------|
| `pwrsply` | V x 10 [0,240] | 18.0 V → `180`  |

### Battery

| Parameter | Range           | Example         |
|-----------|----------------|-----------------|
| `battery` | V x 10 [0,240] | 12.0 V → `120`  |

### Time

| Parameter | Range          | Example         |
|-----------|----------------|----------------|
| `time`    | hhmm [0,2400]  | 14:15 → `1415` |

### Date

| Parameter | Range                      | Example           |
|-----------|----------------------------|-------------------|
| `date`    | yyyymmdd [20210101,21001231]| 2021-12-24 → `20211224` |

### Software Name and Version

| Parameter | Description  | Example                       |
|-----------|--------------|-------------------------------|
| `software`| String (no spaces) | weathercloud_software_v2.4 |

### Software ID

| Parameter    | Description             | Example           |
|--------------|------------------------|-------------------|
| `softwareid` | Assigned software ID    | 123a456b789c      |

---

## Example

```
http://api.weathercloud.net/v01/set/wid/bb34d555d99d93...temp/205/hum/40/bar/10130/wspd/125/wdir/180/...
```

---

> End of *Weathercloud API Documentation v1.0*
