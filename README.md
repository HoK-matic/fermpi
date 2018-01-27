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

Author : Holger Kupke
Date   : 10.01.2018

Copyright (©) 2018 Holger Kupke. All rights reserved.
