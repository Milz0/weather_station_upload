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
