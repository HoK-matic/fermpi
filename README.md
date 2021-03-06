# FermPi  - Fermentation Controller (under development)

This module controls a fermentation process by continously
measuring the temperature and switching the heater socket
on and off to reach or maintain the given temperature.

The controller operates in three different modes:

  - idle mode: the controller just measures the
    current temperatures infinitely and logs them into
    the database.

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

The controller can be managed by a browser based
user interface (see the nstallation instructions below).

Copyright (©) 2018 Holger Kupke. All rights reserved.

##
**Note:**

I am brewing my own beer and was looking for ways to optimize the brewing process. I did not want to buy expensive hardware so I decided to do it on my own. A Rasperry Pi 3 was available. The only additional hardware I needed to buy was a relay board and a temperature sensor for less than €10. I wrote a very basic browser interface, which will be uploaded soon.

When I used this script in early January for the first time, the results were spectacular. The temperatures fluctuate only about 2 to 3 tenth of a degree. It's never been so easy!

## System Requirements:
 * Raspberry Pi
 * Webserver (e.g. Apache2)
 * Python 2.7 (subject to change)
 * **[MySQLdb](https://sourceforge.net/projects/mysql-python/)** driver (subject to change)
 * Adafruit **[W1ThermSensor](https://github.com/timofurrer/w1thermsensor)** library
 * supported sensor device (e.g. **[DS18B20](https://www.ebay.de/itm/DS18B20-Waterproof-Digital-Sensor-Thermal-Probe-Temperature-Thermometer-Arduino-/111431573979)**)
 * 5V relay interface board (e.g. **[SainSmart 2-CH](https://www.ebay.de/i/221441539498?chn=ps)**)
 * Power socket (connected to the relay board)
 
 ## Installation
  * download this repository
  * create the MySQL database (see ***fermpi.sql***)
  * extract the file ***fermpi-ui-v2.tar.gz*** to your web-server's document root or any subdirectory 
  * edit the file ***config.inc.php*** in the ***includes*** directory and fill in your database credentials
  * save the file ***config.inc.php***
  * edit the file ***fermpi.py*** and fill in your database credentials
  * save the file ***fermpi.py***
  * make sure the file ***fermpi.py*** is executable
  * copy the file ***fermpi.py*** to ***/usr/local/bin/***
  * copy the file ***fermpi.service*** to ***/lib/systemd/system/***
  * enable and start the ***fermpi*** service 

If you type in ```sudo systemctl status fermpi.service``` it should say something like this:
```
● fermpi.service - FermPi - Fermentation Controller
   Loaded: loaded (/lib/systemd/system/fermpi.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2018-01-10 10:57:47 CET; 25min 14s ago
 Main PID: 16359 (python)
   CGroup: /system.slice/fermpi.service
           └─16359 python /usr/local/bin/fermpi.py

Jan 10 10:57:47 FermPi systemd[1]: Started FermPi - Fermentation Controller.
```



Happy brewing...
