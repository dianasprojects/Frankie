# FRANKIE

# Custom-Built Astronomical Device for Amateur Astronomy

## Diana Dimitrova

# Introduction

Frankie is a custom-made astronomical device designed to assist amateur astronomers with the align-
ment of their telescopes and to support their observations. It was developed as a teaching project for
astrophysics students, with the aim of providing experience in electronics, MicroPython programming,
3D design and printing, and calculating astronomical parameters.

# Design

## Composition

![Figure_1](https://i.imgur.com/l6dhpTF.jpeg)

As shown in Fig.1, Frankie is composed of a Raspberry Pi Pico 2 microcontroller unit, a BME280 environmental sensor module and an OLED screen
which communicate with the Raspberry Pi via I2C, a NEO-6M GPS module which communicates with the microcontroller via UART, two momentary push-button
switches: one white and one black connected via GPIO, and a USB-C breakout board. The electronics are wrapped in a custom 3D-printed PETG enclosure,
which has an integreated 16mm round spirit level. Frankie does not include an internal battery and is powered either via a wall socket or an external power bank. 

## Computational Implementation

Frankie operates using a main custom-written program, along with one custom-made module and two
pre-existing ones. The GPS Parser Module, adopted unchanged from [1], reads NMEA sentences from
the GPS via UART, and extracts the position, time, date, altitude, speed, and satellite count. The BME
Sensor Module, taken from [2], manages the environmental sensor, providing temperature, pressure,
and humidity readings via I2C. The Celestial Calculations Module, written following Paul Schlyter’s
explanations for computing celestial positions [3], calculates the rise and set times of the Sun, Moon,
and planets for a given day, determines twilight periods, and computes planetary elevations using orbital
mechanics. The output was tested against values found on Stellarium and shown very good levels of
accuracy. The main code then integrates the three modules to display astronomical and environmental
information for the observer’s location on an OLED screen, with automatic cycling and data logging.

# Function

Frankie has three primary functions. First, when placed flat on the telescope’s mount, the integrated spirit
level allows the user to check that it is properly leveled. Furthermore, the device displays the observer’s
latitude, longitude, altitude, UTC time and date, and Local Sidereal Time, which can be useful for the
telescope’s alignment. Second, Frankie also displays real-time environmental parameters, including tem-
perature, humidity, atmospheric pressure, and dew point, all of which can affect the overall image quality.
In addition, the device provides sunrise and sunset times, civil, nautical, and astronomical twilight, the
Moon’s rise and set times, phase, and percent of illumination, as well as the rise, set, and elevation of
the planets, allowing the observer to identify observable targets and best plan for their night of obser-
vations. The display cycles automatically through the screens but can also be manually scrolled using
the black button. Finally, Frankie supports automatic data logging: pressing the white button creates a
time-stamped text file, records observation data periodically, and stops the log when the button is pressed
again or when the device is turned off.

# How to use

Frankie’s environmental sensor is housed in the enclosure, which includes side openings to ensure ac-
curate temperature, humidity, and pressure measurements. To allow the internal air to reach thermal
equilibrium with the outside air, the device should be left outdoors for a while prior to observations.
Moreover, Frankie requires a GPS lock on at least three satellites to operate, which can take up to several
minutes depending on weather conditions. Once the lock is established, a faint blue light will start blink-
ing on the back of the enclosure. The device is optimized for outdoor use but can also operate indoors
when GPS data is available.

# References

[1] Jaryd. How to add gps to a raspberry pi pico. https://core-electronics.com.au/guides/raspberry-pi-pico/how-to-add-gps-to-a-raspberry-pi-pico/, 2025. Accessed: 2025-12-28.

[2] Robert Hamm. Bme280 micropython driver. https://github.com/robert-hh/BME280, 2020. Based on
Bosch BME280 datasheet and Adafruit BME280 Python library. Accessed: 2025-12-28.

[3] Paul Schlyter. Computing planetary positions: a tutorial with worked examples.
https://stjarnhimlen.se/comp/tutorial.html, 2025. Accessed: 2026-01-05.


