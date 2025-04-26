
# Met Office WOW Weather API: Import Protocol Information

> Last Update: June 2024  
> Source: [Met Office WOW Data Formats](https://wow.metoffice.gov.uk/support/dataformats)

## Overview

The Met Office’s Weather Observations Website ([WOW](https://wow.metoffice.gov.uk/)) allows users to submit, view, and share weather observations worldwide. Observations can be uploaded automatically or in bulk using well-defined data formats. This guide outlines the **Bulk Import** and **Automatic Upload** protocols, including supported formats, fields, and submission methods.

---

## Table of Contents

- [Bulk Import](#bulk-import)
  - [Purpose](#bulk-import-purpose)
  - [File Format Specification](#bulk-import-file-format-specification)
  - [Required & Optional Fields](#bulk-import-fields)
  - [Example File](#bulk-import-example)
- [Automatic Upload](#automatic-upload)
  - [Purpose](#automatic-upload-purpose)
  - [API Protocol](#automatic-upload-api-protocol)
  - [Data Fields](#automatic-upload-fields)
  - [Example HTTPS Request](#automatic-upload-example)
- [References](#references)

---

## Bulk Import

### Bulk Import Purpose

Bulk Import is intended for uploading **historical weather observation data** (typically CSV) to a WOW station. It is NOT for ongoing or real-time updates; use Automatic Upload for live/rolling data.

---

### Bulk Import File Format Specification

- **Format:** CSV (comma-separated values)
- **Encoding:** UTF-8 recommended
- **One row per observation**
- **First row:** Header with column names (case insensitive)

#### Required Columns

| Field             | Description               | Example               |
|-------------------|--------------------------|-----------------------|
| `station_name`    | Unique name of station   | MyWeatherStation      |
| `datetime_utc`    | UTC Date/time (ISO 8601) | 2023-07-01T10:00:00Z  |

#### Optional/Recommended Columns

| Field            | Description               | Example   |
|------------------|--------------------------|-----------|
| `air_temperature`| Degrees Celsius (°C)     | 15.7      |
| `dew_point`      | Degrees Celsius          | 12.3      |
| `humidity`       | Percent (%)              | 85        |
| `wind_direction` | Degrees                  | 270       |
| `wind_speed`     | Meters/sec               | 3.4       |
| `pressure`       | hPa                      | 1012.3    |
| `rainfall`       | mm                       | 0.2       |

*See the [official documentation](https://wow.metoffice.gov.uk/support/dataformats#bulk) for the full list of supported fields.*

---

### Bulk Import Example

```csv
station_name,datetime_utc,air_temperature,humidity,wind_speed,wind_direction,pressure,rainfall
MyWeatherStation,2023-06-21T12:00:00Z,17.2,60,4.1,225,1013.4,0.0
MyWeatherStation,2023-06-21T13:00:00Z,18.5,55,3.7,230,1013.1,0.0
```

#### Uploading

1. Log in to WOW.
2. Go to your station's dashboard.
3. Use the “Bulk Upload” feature to submit your CSV file.

---

## Automatic Upload

### Automatic Upload Purpose

For **ongoing, near live or real-time weather observations**, use the Automatic Upload protocol. This is typically done from weather software, IoT devices, or custom scripts that submit observations at regular intervals.

---

### Automatic Upload API Protocol

- **Method:** HTTPS GET (recommended), or HTTPS POST
- **Endpoint:**  
  ```
  https://wow.metoffice.gov.uk/automaticreading
  ```
- **Authentication:** Use the unique **Site ID** and **Authentication Key** from your station’s settings.

#### Required URL Parameters

| Parameter      | Description                     | Example                 |
|----------------|---------------------------------|-------------------------|
| `siteid`       | WOW Station's Site ID           | 1234567                 |
| `siteAuthenticationKey` | Station Auth Key        | abcd1234                |
| `dateutc`      | Date & time in UTC (`YYYY-MM-DD HH:MM:SS`) | 2024-07-01 09:00:00 |
| `tempf`/`tempc`| Temperature (F/°C) (at least one) | 16.3                   |

#### Common Optional Parameters

| Parameter      | Units      | Example   |
|----------------|------------|-----------|
| `humidity`     | %          | 78        |
| `dewptf/dewptc`| F/°C       | 10.3      |
| `windspeedmph/windspeedkmh/windspeedms`| mph/km/h/m/s | 4.5 |
| `winddir`      | Degrees    | 240       |
| `baromin/barommbar` | inHg/mbar | 29.95/1013.8 |
| `rainmm/rainin`| mm/inches  | 0.0       |
| `solarradiation`| W/m²      | 256       |

*For a comprehensive list, see the [official parameters table](https://wow.metoffice.gov.uk/support/dataformats#automatic).*

---

### Automatic Upload Example

HTTPS GET request format:
```
https://wow.metoffice.gov.uk/automaticreading?siteid=1234567&siteAuthenticationKey=abcd1234&dateutc=2024-07-01+09:00:00&tempc=16.3&humidity=78&winddir=240&windspeedms=3.5&barommbar=1013.8&rainmm=0.0
```

---

## References

- [Bulk Import Data Format Documentation](https://wow.metoffice.gov.uk/support/dataformats#bulk)
- [Automatic Upload Data Format Documentation](https://wow.metoffice.gov.uk/support/dataformats#automatic)
- [WOW Support Home](https://wow.metoffice.gov.uk/support)

---

*This document is provided to help you integrate with the Met Office WOW API for uploading weather observation data. Always consult the official documentation for updates or changes to the protocol.*
