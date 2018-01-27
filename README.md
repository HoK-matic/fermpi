# FermPi  - Fermentation Controller (under development)

This module controls a fermentation process by continously
measuring the temperature and switching the heater socket
on and off to reach or maintain the given temperature.

The controller operates in three different modes:
  - constant mode: the controller heats up until the
    given temperature is reached and then maintains this
    temperature until it is switched off or the given
    time limit has been reached. This mode can be used
    e.g. for the fermentation of bread dough

  - gradual mode: the controller heats up and maintains
    consecutive temperature levels. Each level will be
    maintained for a configured period of time before
    heating up to the next level. After the last level
    the heater is switched off. This mode can be used
    e.g. for the mashing process.

  - idle mode: the controller just measures the
    current temperatures infinitely and logs them into
    the database.

The controller will be managed by a browser based
user interface (under development).

Copyright (©) 2018 Holger Kupke. All rights reserved.

##
**Note:**
 * tested on ***RPi-3*** with ***Raspbian Stretch*** and ***Python 2.7***.
##

## System Requirements:
 * Raspberry Pi
 * Adafruit **[W1ThermSensor](https://github.com/timofurrer/w1thermsensor)** library
 * supported sensor device (e.g. DS18B20)
 * 5V relay interface module (e.g. **[SainSmart 2-CH](https://www.amazon.de/SainSmart-Kan%C3%A4le-Relais-Modul-Brett-Arduino-2/dp/B005WR753Q/ref=sr_1_5?ie=UTF8&qid=1517055735&sr=8-5&keywords=relay+module+sainsmart)**
 * **[MySQLdb](https://sourceforge.net/projects/mysql-python/)** (subject to change)
 * Python 2.7 (subject to change)
