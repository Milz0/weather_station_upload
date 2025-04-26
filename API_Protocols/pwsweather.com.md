# PWSweather API Upload Protocol  

This guide explains how to upload weather observations to [PWSweather](https://www.pwsweather.com/) using their HTTP API.  

## API Endpoint

https://pwsupdate.pwsweather.com/api/v1/submitwx


## Required Parameters  

| Parameter           | Description                                                  |  
|---------------------|-------------------------------------------------------------|  
| `action`            | Always set to `updateraw`                                   |  
| `ID`                | Your station ID (as registered on wunderground.com)         |  
| `PASSWORD`          | Your station key (case sensitive)                           |  
| `dateutc`           | Date/time in UTC (`YYYY-MM-DD HH:MM:SS`) or `now`           |  
| `winddir`           | Instantaneous wind direction (0-360°)                       |  
| `windspeedmph`      | Instantaneous wind speed (mph)                              |  
| `windgustmph`       | Current wind gust (mph)                                     |  
| `windgustdir`       | Wind gust direction (0-360°)                                |  
| `windspdmph_avg2m`  | 2-minute average wind speed (mph)                           |  
| `winddir_avg2m`     | 2-minute average wind direction (0-360°)                    |  
| `windgustmph_10m`   | Past 10 minutes wind gust (mph)                             |  
| `windgustdir_10m`   | Past 10 minutes wind gust direction (0-360°)                |  
| `humidity`          | Outdoor humidity (%)                                        |  
| `dewptf`            | Outdoor dewpoint (°F)                                       |  
| `tempf`             | Outdoor temperature (°F)                                    |  
| `rainin`            | Rainfall over the past hour (inches)                        |  
| `dailyrainin`       | Rainfall so far today (inches, local time)                  |  
| `baromin`           | Barometric pressure (inches)                                |  
| `soiltempf`         | Soil temperature (°F)                                       |  
| `solarradiation`    | Solar radiation (W/m²)                                      |  
| `UV`                | UV index                                                    |  
| `softwaretype`      | Name/version of your software                               |  

> **Note:** You may submit only the parameters you have data for.  

---  

## Example API Call

https://pwsupdate.pwsweather.com/api/v1/submitwx?ID=STATIONID&PASSWORD=APIkey&dateutc=2000-12-01+15:20:01&winddir=225&windspeedmph=0.0&windgustmph=0.0&tempf=34.88&rainin=0.06&dailyrainin=0.06&baromin=29.49&dewptf=30.16&humidity=83&solarradiation=183&UV=5.28&softwaretype=Examplever1.1&action=updateraw
