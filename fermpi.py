#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  FermPi - Fermentation Controller

  This script controls a fermentation process by continously
  measuring the temperature and switching the heater socket
  on and off to reach or maintain the given temperature.

  The controller operates in three different modes:
      - constant mode: the controller heats up until the
        given temperature is reached and then maintains this
        temperature until it is switched off or the given
        time limit has been reached. This mode can be used
        e.g. for the fermentation of bread dough

      - gradual mode: the controller heats up and maintains
        consecutive temperatures levels. Each level will be
        maintained for a configured period of time before
        heating up to the next level. After the last level
        the heater is switched off. This mode can be used
        e.g. for the mashing process.

      - idle mode: the controller just measures the
        current temperatures infinitely and logs them into
        the database.

  The controller can be operated by a user interface provided
  as a web page.

  Author : Holger Kupke
  Date   : 23.01.2018

  Copyright (c) 2018 Holger Kupke. All rights reserved.
"""

__version__ = '0.9.1'

import pdb
import sys
import signal
import logging
import threading
import MySQLdb as mdb
import RPi.GPIO as GPIO
from datetime import datetime
from time import mktime, sleep
from optparse import OptionParser

from w1thermsensor import W1ThermSensor

# GPIO port of the relay board
HEATER_GPIO = 21

# database parameters
DB_HOST = '<db server>'
DB_USER = '<db user>'
DB_PWD = '<db password>'
DB_NAME = '<db name>'

# controller states
FPI_STATE_OFF = int(0)
FPI_STATE_ON = int(1)

# controller modes
FPI_MODE_IDLE = int(0)
FPI_MODE_CONSTANT = int(1)
FPI_MODE_GRADUAL = int(2)

# global variables
thread = None


class FermentationThread(threading.Thread):
    """Base class for all operation  modes

       The different operation modes

           - idle mode
           - constant mode
           - levelling mode

       use the same basic functionality to measure the temperature
       and switch the heater on and off. by
       
       Once started, the fermentation thread can be stopped by
       setting it's corresponding event.
    """
    IDLE = 0
    HEATING = 1
    WAITING_FOR_PEAK = 2
    WAITING_FOR_TROUGH = 3

    HEATER_ON = 1
    HEATER_OFF = 0

    def __init__(self, id, gpio):
        """Initialization of class properties

           Args:
               id (long): record id of the given fermentation
               gpio (int): GPIO port of heater relay
        """
        threading.Thread.__init__(self)

        self._logger = logging.getLogger(__name__)
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Initializing thread...")

        self.event = threading.Event()

        self._gpio = gpio                # heater gpio
        self._heater = self.HEATER_OFF   # heater state

        self._id = id                    # fermentation id
        self._name = ''                  # fermentation name
        self._target = float(0)          # target temperature
        self._duration = int(0)          # duration in minutes, 0 = infinitely

        self._cycle = int(10)            # loop timer, default = 10s
        self._overshoot = float(0)       # heater overshoot

        self._sensors = []               # temperature sensors
        self._state = int(0)             # controller state

        self._timestamp = int(0)         # set, when the target temperature is reached

        self._logger.info(" ----------------------------------------")
        self._logger.info(" Initializing sensors...")

        # initializing the temperature sensors
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            i = 0
            for sensor in W1ThermSensor.get_available_sensors():
                if sensor.id not in self._sensors:
                    cur.execute("SELECT * FROM sensors WHERE sensor = '%s'" %(sensor.id))
                    sid = cur.fetchone()[0]
                    if sid is None:
                        cur.execute("INSERT INTO sensors VALUES (0, '%s')" % (sensor.id))
                        cur.execute("SELECT * FROM sensors WHERE sensor = '%s'" %(sensor.id))
                        sid = cur.fetchone()[0]

                self._sensors.append([sensor.id, sid, 0.0, 0.0])
                self._logger.info(" Sensor %d:    %s" % (i+1, self._sensors[i][0]))
                i += 1
        conn.close()

    def _read_temperatures(self):
        """Reading the temperature values of the available sensors.

           The W1ThermSensor-Interface is used to read the temperature
           values of the available sensors. The previous values are
           stored for comparision with the current values.
        """
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Reading sensor values...")

        for i in range(0, len(self._sensors), 4):
            sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, self._sensors[i][0])
            self._sensors[i][3] = self._sensors[i][2]
            self._sensors[i][2] = sensor.get_temperature()

            self._logger.info(" Sensor %s:   %s°C   %s°C" %
                              (self._sensors[i][1],
                               "{:>6.2f}".format(self._sensors[i][2]),
                               "{:>6.2f}".format(self._sensors[i][3])))

        if self._target > 0:
            self._logger.info(" ----------------------------------------")
            self._logger.info(" Target:     %s°C" % ("{:>6.2f}".format(self._target)))
            self._logger.info(" Overshoot:  %s°C" % ("{:>6.2f}".format(self._overshoot)))

    def _log_temperatures(self, ts):
        """Logs the temperature values into the database.

           Args:
               ts (int) = timestamp
        """
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        for i in range(0, len(self._sensors), 4):
            with conn as cur:
                cur.execute("""INSERT INTO logs (fermentation, sensor, temperature, timestamp)
                               VALUES (%s, %s, %1.2f, %d)""" %
                               (self._id, self._sensors[i+1], self._sensors[i+2], ts))
        conn.close

    def _heater_on(self):
        """Switches the heater relay on.

           Since the relay is low-active, the corresponding GPIO is set to high.
           The current heater state is stored.
        """
        GPIO.output(self._gpio, GPIO.LOW)
        self._heater = self.HEATER_ON

    def _heater_off(self):
        """Switches the heater relay off.

           Since the relay is low-active, the corresponding GPIO is set to low.
           The heater state is stored.
        """
        GPIO.output(self._gpio, GPIO.HIGH)
        self._heater = HEATER_OFF


class IdleMode(FermentationThread):
    """Implementation of the fermentation controller's idle mode.

       This mode is used to just log the current temperature values to the
       database.
    """
    def __init__(self, id, gpio):
        FermentationThread.__init__(self, id, gpio)

    def _log_temperatures(self, ts):
        """Logs the current temperature values into the database.

           Args:
               ts (int) = timestamp
        """
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        for i in range(0, len(self._sensors), 4):
            with conn as cur:
                cur.execute("""INSERT INTO logs (fermentation, sensor, temperature, timestamp)
                               VALUES (%s, %s, %1.2f, %d)""" %
                               (self._id, self._sensors[i][1], self._sensors[i][2], ts))
        conn.close

    def run(self):
        """Starts the constant mode thread.

           Heats up to the given target temperature and maintains this
           temperature infinitely (no duration specified), or over a
           given period of time (duration specified),  or until the
           thread is stopped by calling it's <obj>.event.set() function.
        """
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Starting idle mode...")

        # the thread's main loop
        while not self.event.is_set():
            # read current temperatures
            self._read_temperatures()

            # create timestamp
            dt = datetime.utcnow()
            secs = mktime(dt.timetuple())
            ts = int(round(secs))

            # log temperatures
            self._log_temperatures(ts)

            # sleep for the specified cycle time, or until event is set
            self.event.wait(self._cycle)

        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("DELETE FROM logs WHERE fermentation = '0'")
        conn.close()


        self._logger.info(" Leaving idle mode...")


class ConstantMode(FermentationThread):
    """Implementation of the fermentation controller's constant mode.

       This mode is used to heat-up to a given target temperature and
       maintaining this temperature for a given period of time or infinitely.
    """
    def __init__(self, id, gpio):
        FermentationThread.__init__(self, id, gpio)
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Initializing constant mode...")

        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("SELECT * FROM fermentations WHERE id = '%s'" % (self._id))
            row = cur.fetchone()

            if row is not None:
                self._id = int(row[0])
                self._name = row[1]
                if row[2] != None:
                    self._target = float(row[2])
                if row[3] != None:
                    self._duration = int(row[3])

            cur.execute("SELECT id, value FROM config WHERE item = 'overshoot'")
            row = cur.fetchone()
            if row is not None:
               self._overshoot = float(row[1])

            cur.execute("SELECT id, value FROM config WHERE item = 'cycle'")
            row = cur.fetchone()
            if row is not None:
                self._cycle = int(row[1])
        conn.close()

    def _log_temperatures(self, ts):
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        for i in range(0, len(self._sensors), 4):
            with conn as cur:
                cur.execute("""INSERT INTO logs (fermentation, sensor, temperature, timestamp)
                               VALUES (%s, %s, %1.2f, %d)""" %
                               (self._id, self._sensors[i][1], self._sensors[i][2], ts))
        conn.close

    def run(self):
        """Starts the constant mode thread.

           Heats up to the given target temperature and maintains this
           temperature infinitely (no duration specified), or over a
           given period of time (duration specified),  or until the
           thread is stopped by calling it's <obj>.event.set() function.
        """
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Starting constant mode...")

        self._logger.info(" Target:     %s°C" % ("{:>6.2f}".format(self._target)))
        self._logger.info(" Duration:   %s Minute(s)" % ("{:>3d}".format(self._duration)))

        # the thread's main loop
        while not self.event.is_set():
            # read current temperatures
            self._read_temperatures()

            # create timestamp
            dt = datetime.utcnow()
            secs = mktime(dt.timetuple())
            ts = int(round(secs))

            # log temperatures
            self._log_temperatures(ts)

            # check phase
            if self._timestamp == 0:
                # heating up
                if self._sensors[0][2] < (self._target - self._overshoot):
                    if self._heater == self.HEATER_OFF:
                        self._heater_on()
                        self._state = self.HEATING
                elif self._sensors[0][2] < self._sensors[0][3]:
                    if self._heater == self.HEATER_OFF:
                        self._heater_on()
                        self.event.wait(20)
                        self._state = self.HEATING
                elif self._heater == self.HEATER_ON:
                    self._heater_off()
                    self._state == self.WAITING_FOR_PEAK

                if self._sensors[0][2] >= self._target:
                    self._timestamp = ts
                    self._state == self.IDLE
            else:
                # maintain temperature
                if self._duration > 0:
                    # check the current duration
                    m = (ts - self._timestamp) / 60
                    s = (ts - self._timestamp) % 60

                    self._logger.info(" Duration:     %d:%02d Minutes" % (m, s))

                    if m >= self._duration:
                        # duration limit reached
                        if self._heater == self.HEATER_ON:
                            self._heater_off()
                            sefl._state = self.IDLE

                        # end thread
                        break

                # keep on going
                if self._sensors[0][2] <= (self._target - 0.10):
                    # temperature is below threshold
                    if self._sensors[0][2] < self._sensors[0][3]:
                        # temperature is decreasing
                        self._heater_on()
                        self.event.wait(10)
                        self._heater_off()
                        self._state = self.WAITING_FOR_PEAK

            self._logger.info(" ----------------------------------------")
            if self._state is self.HEATING:
                self._logger.info(" State: heating...")
            elif self._state is self.WAITING_FOR_PEAK:
                self._logger.info(" State: waiting for peak...")
            elif self._state is self.WAITING_FOR_TROUGH:
                self._logger.info(" State: heating, waiting for trough...")
            elif self._state is self.IDLE:
                self._logger.info(" State: idle...")

            # sleep for the specified cycle time, or until event is set
            self.event.wait(self._cycle)

        # reset configuration
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("UPDATE config SET value = '0' WHERE item = 'mode'")
            cur.execute("UPDATE config SET value = '0' WHERE item = 'log'")
        conn.close()

        self._logger.info(" Leaving constant mode...")


class GradualMode(FermentationThread):
    """Implementation of the fermentation controller's gradual mode.

       The controller heats up and maintains consecutive temperature
       levels. Each level will be maintained for a configured period
       of time before heating up to the next level. After the last
       level, the heater is switched off. This mode can be used e.g.
       for the mashing process.
    """
    def __init__(self, id, gpio):
        FermentationThread.__init__(self, id, gpio)
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Initializing gradual mode...")

        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("SELECT * FROM fermentations WHERE id = '%s'" % (self._id))
            row = cur.fetchone()

            if row is not None:
                self._id = int(row[0])
                self._name = row[1]
                if row[2] != None:
                    self._target = float(row[2])
                if row[3] != None:
                    self._duration = int(row[3])

            cur.execute("SELECT id, value FROM config WHERE item = 'overshoot'")
            row = cur.fetchone()
            if row is not None:
               self._overshoot = float(row[1])

            cur.execute("SELECT id, value FROM config WHERE item = 'cycle'")
            row = cur.fetchone()
            if row is not None:
                self._cycle = int(row[1])
        conn.close()

    def _log_temperatures(self, ts):
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        for i in range(0, len(self._sensors), 4):
            with conn as cur:
                cur.execute("""INSERT INTO logs (fermentation, sensor, temperature, timestamp)
                               VALUES (%s, %s, %1.2f, %d)""" %
                               (self._id, self._sensors[i][1], self._sensors[i][2], ts))
        conn.close

    def _get_next_level(self):
        bNext = False

        self._target = float(0)
        self._duration = int(0)
        self._timestamp = int(0)

        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("SELECT * FROM fermentations WHERE id = '%s'" % (self._id))
            row = cur.fetchone()

            if row is not None:
                i = 2
                while i < 11:
                    if row[i] >= self._target:
                        self._target = float(row[i])

                        if row[i+1] != None:
                            self._duration = int(row[i+1])

                        bNext = True
                        break
                    else:
                        i += 2
                    # end if
                # end while
            # end if
        # end with
        conn.close()

        return bNext

    def run(self):
        """Starts the gradual  mode thread.

           The controller heats up and maintains consecutive temperature
           levels.
        """
        self._logger.info(" ----------------------------------------")
        self._logger.info(" Starting gradual mode...")

        self._logger.info(" Target:     %s°C" % ("{:>6.2f}".format(self._target)))
        self._logger.info(" Duration:   %s Minute(s)" % ("{:>3d}".format(self._duration)))

        # the thread's main loop
        while not self.event.is_set():
            # read current temperatures
            self._read_temperatures()

            # create timestamp
            dt = datetime.utcnow()
            secs = mktime(dt.timetuple())
            ts = int(round(secs))

            # log temperatures
            self._log_temperatures(ts)

            # check phase
            if self._timestamp == 0:
                # heating up
                if self._sensors[0][2] < (self._target - self._overshoot):
                    if self._heater == self.HEATER_OFF:
                        self._heater_on()
                        self._state = self.HEATING
                elif self._sensors[0][2] < self._sensors[0][3]:
                    if self._heater == self.HEATER_OFF:
                        self._heater_on()
                        self.event.wait(20)
                        self._state = self.HEATING
                elif self._heater == self.HEATER_ON:
                    self._heater_off()
                    self._state == self.WAITING_FOR_PEAK

                if self._sensors[0][2] >= self._target:
                    self._timestamp = ts
                    self._state == self.IDLE
            else:
                # maintain temperature
                if self._duration > 0:
                    # check the current duration
                    m = (ts - self._timestamp) / 60
                    s = (ts - self._timestamp) % 60

                    self._logger.info(" Duration:     %d:%02d Minutes" % (m, s))

                    if m >= self._duration:
                        # duration limit reached
                        if self._get_next_level() is False:
                            if self._heater == self.HEATER_ON:
                                self._heater_off()
                                sefl._state = self.IDLE

                            # end thread
                            break

                # keep on going
                if self._sensors[0][2] <= (self._target - 0.10):
                    # temperature is below threshold
                    if self._sensors[0][2] < self._sensors[0][3]:
                        # temperature is decreasing
                        self._heater_on()
                        self.event.wait(10)
                        self._heater_off()
                        self._state = self.WAITING_FOR_PEAK

            self._logger.info(" ----------------------------------------")
            if self._state is self.HEATING:
                self._logger.info(" State: heating...")
            elif self._state is self.WAITING_FOR_PEAK:
                self._logger.info(" State: waiting for peak...")
            elif self._state is self.WAITING_FOR_TROUGH:
                self._logger.info(" State: heating, waiting for trough...")
            elif self._state is self.IDLE:
                self._logger.info(" State: idle...")

            # sleep for the specified cycle time, or until event is set
            self.event.wait(self._cycle)

        # reset configuration
        conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
        with conn as cur:
            cur.execute("UPDATE config SET value = '0' WHERE item = 'mode'")
            cur.execute("UPDATE config SET value = '0' WHERE item = 'log'")
        conn.close()

        self._logger.info(" Leaving constant mode...")


def heater_off():
    """Switch heater GPIO port off"""
    GPIO.output(HEATER_GPIO, GPIO.HIGH)

def on_exit(sig, frame):
    """Clean up on exit"""
    global thread

    logger = logging.getLogger(__name__)

    # cleaning up
    logger.info("\r                                                           ")
    logger.info(" Cleaning up...")

    # exit threads, if any
    if thread is not None:
        logger.info(" Stopping thread...")
        thread.event.set()
        while thread.is_alive():
            thread.join(0.5)
        thread = None

    # resetting GPIOs
    heater_off()
    GPIO.cleanup()

    # exitting process
    logger.info(" Bye.")
    sys.exit(0)

def read_configuration():
    """Reads the configuration parameters from the database"""
    config = {}

    conn = mdb.connect(DB_HOST, DB_USER, DB_PWD, DB_NAME)
    with conn as cur:
        cur.execute("SELECT item, value FROM config WHERE 1")
        row = cur.fetchone()
        while row is not None:
            if row[0] == 'state':
                config['state'] = int(row[1])
                if config['state'] == FPI_STATE_OFF:
                    config['mode']= FPI_MODE_IDLE
                    config['cycle'] = int(10)
                    config['log'] = int(0)
                    break
            elif row[0] == 'mode':
                config['mode']= int(row[1])
            elif row[0] == 'cycle':
                config['cycle'] = int(row[1])
            elif row[0] == 'log':
                config['log'] = int(row[1])
            row = cur.fetchone()
        # end while
    # end with
    conn.close
    return config

def main():
    global thread

    # register exit handler
    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    # check commandline parameters
    parser = OptionParser()
    parser.add_option("-d", "--debug", dest="debug", action="store_true", default="False", help="print debug information to stdout")
    (options, args) = parser.parse_args(sys.argv)

    if options.debug is True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    logger = logging.getLogger(__name__)
    logger.info(" FermPi - Fermentaion Controller")
    logger.info(" Copyright (c) 2018 Holger Kupke")

    # init gpio interface
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # init relay(s)
    GPIO.setup(HEATER_GPIO, GPIO.OUT)
    heater_off()

    while True:
        try:
            config = read_configuration()

            if config['state'] == FPI_STATE_OFF:
                if thread is None:
                    logger.info(" ----------------------------------------")
                    logger.info(" State: OFF")
                else:
                    logger.info(" ----------------------------------------")
                    logger.info(" Stopping current thread...")
                    thread.event.set()
                    while thread.is_alive():
                        thread.join(1.0)
                    thread = None
            elif config['state'] == FPI_STATE_ON:
                if thread is None:
                    logger.info(" ----------------------------------------")
                    logger.info(" State: ON")
                    if config['mode'] == FPI_MODE_IDLE:
                        thread = IdleMode(0, 0)
                        thread.start()
                    elif config['mode'] == FPI_MODE_CONSTANT:
                        thread = ConstantMode(config['log'], HEATER_GPIO)
                        thread.start()
                    elif config['mode'] == FPI_MODE_GRADUAL:
                        thread = GradualMode(config['log'], HEATER_GPIO)
                        thread.start()
            else:
                logger.warning(" Unknown controller state (%d)" % (config['state']))

        except mdb.Error as e:
            logger.error(" SQL Fehler   :%d -  %s" % (e.args[0], e.args[1]))
            if conn:
                conn.close()
                conn = None

        sleep(float(config['cycle']))

if __name__ == '__main__':
    main()
