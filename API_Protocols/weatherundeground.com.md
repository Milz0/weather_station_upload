# Weather Underground (Wunderground) Weather Station Upload API Protocol

Comprehensive documentation of the realtime Personal Weather Station (PWS) upload protocol and all available parameters.

---

## Overview

Weather Underground provides an HTTP(S) API to allow personal weather stations to send live, minute-by-minute observations. The protocol is used by custom weather station hardware, Raspberry Pi projects, Arduino code, or any custom script that measures weather.

---

## API Endpoint

```plaintext
http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php
```

---

## HTTP Method

- **GET** (Parameters are passed in the URL)

---

## Required Parameters

| Parameter    | Type/Format  | Description         |
| ------------ | ------------ | -------------------|
| ID           | String       | PWS Station ID      |
| PASSWORD     | String       | PWS Station Key     |
| dateutc      | now or `YYYY-MM-DD HH:MM:SS` (UTC) | Date/time of reading (UTC) |
| action       | `updateraw`  | Always required     |

---

## Full Parameter List

| Parameter           | Unit/Format         | Description                                                                |
|---------------------|--------------------|----------------------------------------------------------------------------|
| ID                  | String             | PWS Station ID (required)                                                  |
| PASSWORD            | String             | PWS Station Key/Password (required)                                        |
| dateutc             | now or `YYYY-MM-DD HH:MM:SS`(UTC) | Obs time (UTC, required)                                |
| action              | updateraw          | Always updateraw (required)                                                |
| tempf               | °F                 | Outdoor temperature                                                        |
| humidity            | %                  | Outdoor humidity                                                           |
| dewptf              | °F                 | Dew point                                                                  |
| windchillf          | °F                 | Wind chill temperature                                                     |
| winddir             | degrees            | Wind direction                                                             |
| windspeedmph        | mph                | Wind speed                                                                 |
| windgustmph         | mph                | Wind gust                                                                  |
| rainin              | in                 | Rain in last interval (since last upload)                                  |
| dailyrainin         | in                 | Rain since midnight local time                                             |
| weeklyrainin        | in                 | Rain in last 7 days                                                        |
| monthlyrainin       | in                 | Rain in current calendar month                                             |
| yearlyrainin        | in                 | Rain in current year                                                       |
| baromin             | inHg               | Barometric pressure                                                        |
| absbaromin          | inHg               | Absolute barometric pressure                                               |
| solarradiation      | W/m^2              | Solar radiation                                                            |
| UV                  | index value        | UV index                                                                   |
| indoortempf         | °F                 | Indoor temperature                                                         |
| indoorhumidity      | %                  | Indoor humidity                                                            |
| leafwetness         | Integer/Steps      | Leaf wetness sensor                                                        |
| soiltempf           | °F                 | Soil temperature                                                           |
| soilmoisture        | Integer or %       | Soil moisture                                                              |
| lowbatt             | 0 or 1             | Low battery indicator (1 = low, 0 = normal)                                |
| sensorstatus        | Integer/flags      | Sensor status or errors                                                    |
| softwaretype        | String             | Name/Version of uploading software/hardware                                |
| realtime            | 1                  | Set 1 for rapid-fire/Real Time updates                                     |
| rtfreq              | Integer (sec)      | Rapid-Fire update frequency (ex. 2 for every 2 seconds)                    |
| windspdmph_avg2m    | mph                | Avg wind speed over 2 minutes                                              |
| windgustmph_10m     | mph                | Max wind gust in 10 minutes                                                |
| maxdailygust        | mph                | Max gust so far today                                                      |
| eventrainin         | in                 | Event precipitation total since last reset                                 |

---

## Special Notes

- Only `ID`, `PASSWORD`, `dateutc`, and `action` are strictly required.
- All other parameters are optional and can be omitted if your hardware does not support them.
- Use `dateutc=now` for the current UTC time, or provide UTC time as `YYYY-MM-DD HH:MM:SS`.
- URLs **must be URL encoded** (for example, spaces as `%20`).

---

## Example: Full Upload

```plaintext
http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?ID=MYSTATION&PASSWORD=mykey&dateutc=now&tempf=70.1&humidity=52&dewptf=50.7&winddir=190&windspeedmph=5.1&windgustmph=7.9&rainin=0.00&dailyrainin=0.00&solarradiation=750&UV=3&baromin=29.94&indoortempf=69.3&indoorhumidity=38&softwaretype=MyCustomPiWeather1.1&action=updateraw
```

---

## Responses

- **On Success:**  
  ```
  success
  ```
- **On Error:**  
  ```
  Password incorrect
  ```

---

## References

- [Official Wunderground PWS Upload Protocol Documentation](https://support.weather.com/s/article/PWS-Upload-Protocol?language=en_US)[^2](https://support.weather.com/s/article/PWS-Upload-Protocol?language=en_US)
- [Weather Underground PWS API library for Node.js (community)](https://github.com/brbeaird/wunderground-upload)[^1](https://github.com/brbeaird/wunderground-upload)
- [WXForum community WU protocol notes](https://www.wxforum.net/index.php?topic=35094.0)

---

## License

This documentation is provided for community use.
