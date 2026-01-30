from machine import Pin, UART, I2C
import framebuf
import time
import gps_parser
import bme280
import os
import math
import celestial_calculations

# -------------------------
# TWILIGHT DRAWING
# -------------------------

def draw_twilight_screen(display, title, morning_time, evening_time):
    display.fill(0)
    
    # Title centered at top
    title_x = (128 - len(title) * 8) // 2
    display.text(title, title_x, 5, 1)
    
    # Display morning and evening intervals
    morning_text = "{}".format(morning_time)
    evening_text = "{}".format(evening_time)
    
    morning_x = (128 - len(morning_text) * 8) // 2
    evening_x = (128 - len(evening_text) * 8) // 2
    
    display.text(morning_text, morning_x, 28, 1)
    display.text(evening_text, evening_x, 40, 1)
    
    display.show()

# -------------------------
# SUN DRAWING
# -------------------------

def draw_sun_screen(display, rise_time, set_time):
    display.fill(0)
    
    # Title centered at top
    title = "Sun"
    title_x = (128 - len(title) * 8) // 2
    display.text(title, title_x, 5, 1)
    
    # Draw sun on the left side
    sun_center_x = 20
    sun_center_y = 35
    sun_radius = 10
    
    # Draw sun circle
    for angle in range(0, 360, 10):
        rad = angle * 3.14159 / 180
        x = int(sun_center_x + sun_radius * math.cos(rad))
        y = int(sun_center_y + sun_radius * math.sin(rad))
        display.fb.pixel(x, y, 1)
    
    # Fill sun circle
    for y in range(sun_center_y - sun_radius, sun_center_y + sun_radius):
        dy = y - sun_center_y
        if abs(dy) < sun_radius:
            dx = int(math.sqrt(sun_radius * sun_radius - dy * dy))
            for x in range(sun_center_x - dx, sun_center_x + dx + 1):
                display.fb.pixel(x, y, 1)
    
    # Draw sun rays
    ray_length = 5
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = angle * 3.14159 / 180
        x1 = int(sun_center_x + (sun_radius + 2) * math.cos(rad))
        y1 = int(sun_center_y + (sun_radius + 2) * math.sin(rad))
        x2 = int(sun_center_x + (sun_radius + 2 + ray_length) * math.cos(rad))
        y2 = int(sun_center_y + (sun_radius + 2 + ray_length) * math.sin(rad))
        display.fb.line(x1, y1, x2, y2, 1)
    
    # Display rise and set times to the right
    rise_text = "Rise:{}".format(rise_time)
    set_text = "Set: {}".format(set_time)
    
    # Center the text on the right side
    text_x = 40
    display.text(rise_text, text_x, 28, 1)
    display.text(set_text, text_x, 40, 1)
    
    display.show()

# -------------------------
# MOON RISE/SET DRAWING
# -------------------------

def draw_moon_screen(display, rise_time, set_time):
    display.fill(0)
    
    # Title centered at top
    title = "Moon"
    title_x = (128 - len(title) * 8) // 2
    display.text(title, title_x, 5, 1)
    
    # Draw moon (waxing crescent) on the left side
    moon_center_x = 20
    moon_center_y = 35
    moon_radius = 10
    
    # Draw moon circle outline
    for angle in range(0, 360, 10):
        rad = angle * 3.14159 / 180
        x = int(moon_center_x + moon_radius * math.cos(rad))
        y = int(moon_center_y + moon_radius * math.sin(rad))
        display.fb.pixel(x, y, 1)
    
    # Fill waxing crescent (right side partial fill)
    for y in range(moon_center_y - moon_radius, moon_center_y + moon_radius):
        dy = y - moon_center_y
        if abs(dy) < moon_radius:
            dx = int(math.sqrt(moon_radius * moon_radius - dy * dy))
            for x in range(moon_center_x + int(dx * 0.5), moon_center_x + dx + 1):
                display.fb.pixel(x, y, 1)
    
    # Display rise and set times to the right
    rise_text = "Rise:{}".format(rise_time)
    set_text = "Set: {}".format(set_time)
    
    # Center the text on the right side
    text_x = 40
    display.text(rise_text, text_x, 28, 1)
    display.text(set_text, text_x, 40, 1)
    
    display.show()

# -------------------------------------------
# DEW POINT CALCULATION
# -------------------------------------------

def calculate_dew_point(T, RH):
    if T is None or RH is None:
        return None
    
    if T >= 0:
        a = 17.27
        b = 237.7
    else:
        a = 17.84
        b = 245.42
    
    gamma = math.log(RH / 100) + (a * T) / (b + T)
    Td = (b * gamma) / (a - gamma)
    return round(Td, 2)


# Initializing buttons
white = Pin(4, Pin.IN, Pin.PULL_UP)
black   = Pin(16, Pin.IN, Pin.PULL_UP)

last_green = 1
last_red = 1
debounce = 0.05

# Logging state variables
logging_active = False
last_log_time = 0
log_interval = 300  # seconds

# -------------------------
# DISPLAY SETUP
# -------------------------
    
i2c_display = I2C(1, scl=Pin(15), sda=Pin(14))  
OLED_ADDR = 0x3C

class SSD1309:
    def __init__(self, width, height, i2c, addr=OLED_ADDR):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = bytearray(self.width * self.pages)
        self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto_mem(self.addr, 0x80, bytearray([cmd]))

    def write_data(self, buf):
        self.i2c.writeto_mem(self.addr, 0x40, buf)

    def init_display(self):
        for cmd in (
            0xAE, 0xD5,0x80,0xA8,self.height-1,0xD3,0x00,
            0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,
            0x81,0xFF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0xAF
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def fill(self, color):
        self.fb.fill(color)

    def text(self, string, x, y, color=1):
        self.fb.text(string, x, y, color)

    def show(self):
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            start = self.width * page
            end = start + self.width
            self.write_data(self.buffer[start:end])

oled = SSD1309(128, 64, i2c_display)

# -------------------------
# BME280 SENSOR SETUP
# -------------------------

i2c_sensor = I2C(0, sda=Pin(12), scl=Pin(13))  

# Initialize BME280 sensor
bme_sensor = None
try:
    bme_sensor = bme280.BME280(i2c=i2c_sensor)
    print("BME280 initialized successfully!")
except Exception as e:
    print("Error initializing BME280:", e)
    print("Sensor readings will show as ---")

# Global variables for sensor data
temperature = None
humidity = None
pressure_hpa = None
dew_point = None

def read_bme280():
    global temperature, humidity, pressure_hpa, dew_point
    
    if bme_sensor is None:
        temperature = None
        humidity = None
        pressure_hpa = None
        dew_point = None
        return
    
    try:
        data = bme_sensor.read_compensated_data()
        temperature = data[0]
        humidity = data[2]
        pressure_hpa = data[1] / 100
        dew_point = calculate_dew_point(temperature, humidity)
    except Exception as e:
        print("Error reading BME280:", e)
        temperature = None
        humidity = None
        pressure_hpa = None

# -------------------------
# GPS SETUP
# -------------------------

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
gps = gps_parser.GPSReader(uart)

current_screen = 1
last_screen_switch = time.time()
screen_interval = 10

# -------------------------
# SUN/MOON RISE/SET CALCULATION
# -------------------------

planet_calc = None
sun_rise = "---"
sun_set = "---"
last_sun_calc_date = None

civil_dawn = "---"
civil_dusk = "---"
nautical_dawn = "---"
nautical_dusk = "---"
astro_dawn = "---"
astro_dusk = "---"

moon_rise = "---"
moon_set = "---"
last_moon_calc_date = None

planets_list = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
planet_data = {
    "Mercury": {"rise": "---", "set": "---", "elevation": "---"},
    "Venus": {"rise": "---", "set": "---", "elevation": "---"},
    "Mars": {"rise": "---", "set": "---", "elevation": "---"},
    "Jupiter": {"rise": "---", "set": "---", "elevation": "---"},
    "Saturn": {"rise": "---", "set": "---", "elevation": "---"},
    "Uranus": {"rise": "---", "set": "---", "elevation": "---"},
    "Neptune": {"rise": "---", "set": "---", "elevation": "---"}
}
last_planet_calc_date = None
last_planet_elevation_update = 0
planet_elevation_interval = 60

def update_sun_times(gps_data):
    global planet_calc, sun_rise, sun_set, last_sun_calc_date
    global civil_dawn, civil_dusk, nautical_dawn, nautical_dusk, astro_dawn, astro_dusk
    
    if not gps_data.has_fix or gps_data.date is None:
        return
    
    if last_sun_calc_date == gps_data.date:
        return
    
    try:
        date_parts = gps_data.date.split('/')
        if len(date_parts) != 3:
            return
        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])
        
        planet_calc = celestial_calculations.PlanetCalculator(
            lat=gps_data.latitude,
            lon=gps_data.longitude
        )
        
        twilight_times = planet_calc.calculate_twilight_times(day, month, year)
        
        if twilight_times['astronomical_dawn']['status'] == 'normal':
            astro_begin = twilight_times['astronomical_dawn']['rise']
            astro_end = twilight_times['astronomical_dawn']['set']
            naut_begin = twilight_times['nautical_dawn']['rise']
            naut_end = twilight_times['nautical_dawn']['set']
            civil_begin = twilight_times['civil_dawn']['rise']
            civil_end = twilight_times['civil_dawn']['set']
            sunrise_time = twilight_times['sunrise']['rise']
            sunset_time = twilight_times['sunrise']['set']
            
            sun_rise = sunrise_time
            sun_set = sunset_time
            
            civil_dawn = "{}-{}".format(civil_begin, sunrise_time)
            civil_dusk = "{}-{}".format(sunset_time, civil_end)
            
            nautical_dawn = "{}-{}".format(naut_begin, civil_begin)
            nautical_dusk = "{}-{}".format(civil_end, naut_end)
            
            astro_dawn = "{}-{}".format(astro_begin, naut_begin)
            astro_dusk = "{}-{}".format(naut_end, astro_end)
            
        else:
            sun_rise = "---"
            sun_set = "---"
            civil_dawn = "---"
            civil_dusk = "---"
            nautical_dawn = "---"
            nautical_dusk = "---"
            astro_dawn = "---"
            astro_dusk = "---"
        
        last_sun_calc_date = gps_data.date
        
        
    except Exception as e:
        print("Error calculating sun times:", e)

def update_moon_times(gps_data):
    global moon_rise, moon_set, last_moon_calc_date, planet_calc
    
    if not gps_data.has_fix or gps_data.date is None:
        return
    
    if last_moon_calc_date == gps_data.date:
        return
    
    try:
        date_parts = gps_data.date.split('/')
        if len(date_parts) != 3:
            return
        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])
        
        if planet_calc is None:
            planet_calc = celestial_calculations.PlanetCalculator(
                lat=gps_data.latitude,
                lon=gps_data.longitude
            )
        
        moon_times = planet_calc.calculate_moon_rise_set(day, month, year)
        
        
        if moon_times['status'] == 'normal':
            moon_rise = moon_times['rise'] if moon_times['rise'] else "---"
            moon_set = moon_times['set'] if moon_times['set'] else "---"
        else:
            moon_rise = "---"
            moon_set = "---"
        
       
        last_moon_calc_date = gps_data.date
        
        
    except Exception as e:
        print("Error calculating moon times:", e)


def update_planet_rise_set(gps_data):
    global planet_data, last_planet_calc_date, planet_calc
    
    if not gps_data.has_fix or gps_data.date is None:
        return
    
    if last_planet_calc_date == gps_data.date:
        return
    
    try:
        date_parts = gps_data.date.split('/')
        if len(date_parts) != 3:
            return
        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])
        
        if planet_calc is None:
            planet_calc = celestial_calculations.PlanetCalculator(
                lat=gps_data.latitude,
                lon=gps_data.longitude
            )
        
        for planet_name in planets_list:
            try:
                rise_set = planet_calc.calculate_planet_rise_set(planet_name, day, month, year)
                
                if rise_set and rise_set['status'] == 'normal':
                    planet_data[planet_name]['rise'] = rise_set['rise']
                    planet_data[planet_name]['set'] = rise_set['set']
                else:
                    planet_data[planet_name]['rise'] = "---"
                    planet_data[planet_name]['set'] = "---"
                    
            except Exception as e:
                print("Error calculating {} rise/set: {}".format(planet_name, e))
                planet_data[planet_name]['rise'] = "---"
                planet_data[planet_name]['set'] = "---"
        
        last_planet_calc_date = gps_data.date
        
        
    except Exception as e:
        print("Error calculating planet rise/set:", e)

def update_planet_elevations(gps_data):
    global planet_data, last_planet_elevation_update
    
    if not gps_data.has_fix or gps_data.date is None or gps_data.time is None:
        return
    
    current_time = time.time()
    if last_planet_elevation_update != 0 and current_time - last_planet_elevation_update < planet_elevation_interval:
        return
    
    try:
        date_parts = gps_data.date.split('/')
        if len(date_parts) != 3:
            return
        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])
        
        time_parts = gps_data.time.split(':')
        if len(time_parts) >= 3:
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            second = int(float(time_parts[2].split('.')[0]))
        else:
            return
        
        # Calculate LST using the main code's method (which works!)
        lst_string = get_lmst(gps_data.longitude, gps_data.date, gps_data.time)
        
        # Convert LST from "HH:MM:SS" to degrees
        if lst_string != "---":
            lst_parts = lst_string.split(':')
            lst_hours = int(lst_parts[0]) + int(lst_parts[1])/60.0 + int(lst_parts[2])/3600.0
            lst_deg = lst_hours * 15.0  # Convert hours to degrees
        else:
            return
        
        elev_calc = celestial_calculations.PlanetCalculator(
            lat=gps_data.latitude,
            lon=gps_data.longitude
        )
        
        for planet_name in planets_list:
            try:
                # Calculate RA and Dec
                planet_info = elev_calc.calculate_planet(planet_name, day, month, year, hour, minute, second)
                
                if planet_info and 'ra' in planet_info and 'dec' in planet_info:
                    # Use the accurate LST from main code instead of the one from calculate_planet
                    altitude = elev_calc.calc_altitude(planet_info['ra'], planet_info['dec'], lst_deg)
                    planet_data[planet_name]['elevation'] = "{:.1f}".format(altitude)
                else:
                    planet_data[planet_name]['elevation'] = "---"
                    
            except Exception as e:
                print("Error calculating {} elevation: {}".format(planet_name, e))
                planet_data[planet_name]['elevation'] = "---"
        
        last_planet_elevation_update = current_time
        
    except Exception as e:
        print("Error calculating planet elevations:", e)

# -------------------------
# MOON PHASE CALCULATION
# -------------------------

ref_year = 2026
ref_month = 1
ref_day = 18
ref_hour = 20
ref_minute = 52
ref_phase_angle = 0

synodic_month = 29.530588853
month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def date_to_total_days(year, month, day, hour, minute):
    days = sum(month_days[:month-1]) + (day - 1)
    days += hour / 24 + minute / 1440
    return days

def get_phase_name(angle):
    if angle < 18 or angle >= 342:
        return "New Moon"
    elif angle < 84:
        return "Waxing Crescent"
    elif angle < 96:
        return "First Quarter"
    elif angle < 162:
        return "Waxing Gibbous"
    elif angle < 198:
        return "Full Moon"
    elif angle < 264:
        return "Waning Gibbous"
    elif angle < 276:
        return "Last Quarter"
    else:
        return "Waning Crescent"


def calculate_moon_phase(date_str, time_str):
    global moon_illumination
    
    try:
        if date_str is None or date_str == "":
            moon_illumination = "----"
            return "----"
        date_parts = date_str.split('/')
        if len(date_parts) != 3:
            moon_illumination = "----"
            return "----"
        current_day = int(date_parts[0])
        current_month = int(date_parts[1])
        current_year = int(date_parts[2])
        
        if current_year != 2026:
            moon_illumination = "Year != 2026"
            return "Year != 2026"
        
        if time_str is None or time_str == "":
            moon_illumination = "----"
            return "----"
        time_parts = time_str.split(':')
        if len(time_parts) != 3:
            moon_illumination = "----"
            return "----"
        current_hour = int(time_parts[0])
        current_minute = int(time_parts[1])
        seconds = int(float(time_parts[2].split('.')[0])) + 2
        
        if seconds >= 60:
            seconds -= 60
            current_minute += 1
        if current_minute >= 60:
            current_minute -= 60
            current_hour += 1
        if current_hour >= 24:
            current_hour -= 24
        
        ref_decimal = date_to_total_days(ref_year, ref_month, ref_day, ref_hour, ref_minute)
        current_decimal = date_to_total_days(current_year, current_month, current_day, current_hour, current_minute)
        
        days_elapsed = current_decimal - ref_decimal
        days_in_cycle = days_elapsed % synodic_month
        phase_angle = (ref_phase_angle + 360 * (days_in_cycle / synodic_month)) % 360
        
        # Calculate illumination percentage
        phase_angle_rad = phase_angle * 3.14159 / 180
        illumination = (1 - math.cos(phase_angle_rad)) / 2 * 100
        moon_illumination = "{:.0f}%".format(illumination)
        
        phase_name = get_phase_name(phase_angle)
        
        return phase_name
        
    except Exception as e:
        print("Moon phase error:", e)
        moon_illumination = "----"
        return "----"

moon_phase_history = []
moon_phase = "----"
moon_illumination = "----"
last_moon_calc = 0

def check_datetime_stability(date_str, time_str):
    global moon_phase_history
    
    if date_str is None or date_str == "" or time_str is None or time_str == "":
        moon_phase_history = []
        return False
    
    try:
        time_parts = time_str.split(':')
        if len(time_parts) < 2:
            moon_phase_history = []
            return False
    except:
        moon_phase_history = []
        return False
    
    return True

def update_moon_phase(date_str, time_str):
    global moon_phase, last_moon_calc
    
    if date_str is None or date_str == "" or time_str is None or time_str == "":
        return
    
    current_time = time.time()
    is_stable = check_datetime_stability(date_str, time_str)
    
    if not is_stable:
        return
    
    if last_moon_calc == 0 or current_time - last_moon_calc >= 14400:
        moon_phase = calculate_moon_phase(date_str, time_str)
        last_moon_calc = current_time
        print("Moon phase calculated:", moon_phase)

# -------------------------
# MOON PHASE DRAWING
# -------------------------

def draw_moon_phase(display, phase_name):
    display.fill(0)
    
    display.text("Moon", 0, 0, 1)
    display.text("Phase", 128 - 5*8, 0, 1)
    
    center_x = 64
    center_y = 28
    radius = 18
    
    for angle in range(0, 360, 5):
        rad = angle * 3.14159 / 180
        x = int(center_x + radius * math.cos(rad))
        y = int(center_y + radius * math.sin(rad))
        display.fb.pixel(x, y, 1)
    
    if phase_name == "New Moon":
        pass
    elif phase_name == "Waxing Crescent":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x + int(dx * 0.5), center_x + dx + 1):
                    display.fb.pixel(x, y, 1)
    elif phase_name == "First Quarter":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x, center_x + dx + 1):
                    display.fb.pixel(x, y, 1)
    elif phase_name == "Waxing Gibbous":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x - dx, center_x + dx + 1):
                    display.fb.pixel(x, y, 1)
                for x in range(center_x - dx, center_x - int(dx * 0.5)):
                    display.fb.pixel(x, y, 0)
    elif phase_name == "Full Moon":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x - dx, center_x + dx + 1):
                    display.fb.pixel(x, y, 1)
    elif phase_name == "Waning Gibbous":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x - dx, center_x + dx + 1):
                    display.fb.pixel(x, y, 1)
                for x in range(center_x + int(dx * 0.5), center_x + dx + 1):
                    display.fb.pixel(x, y, 0)
    elif phase_name == "Last Quarter":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x - dx, center_x + 1):
                    display.fb.pixel(x, y, 1)
    elif phase_name == "Waning Crescent":
        for y in range(center_y - radius, center_y + radius):
            dy = y - center_y
            if abs(dy) < radius:
                dx = int(math.sqrt(radius * radius - dy * dy))
                for x in range(center_x - dx, center_x - int(dx * 0.5)):
                    display.fb.pixel(x, y, 1)
    
    text_x = center_x - len(phase_name) * 4
    display.text(phase_name, text_x, 56, 1)
    display.show()

# -------------------------
# MOON ILLUMINATION DRAWING
# -------------------------

def draw_moon_illumination(display, illumination):
    display.fill(0)
    
    # Title
    title = "Moon"
    title_x = (128 - len(title) * 8) // 2
    display.text(title, title_x, 13, 1)  # Changed from 5 to 13
    
    # Subtitle
    subtitle = "Illumination"
    subtitle_x = (128 - len(subtitle) * 8) // 2
    display.text(subtitle, subtitle_x, 28, 1)  # Changed from 20 to 28
    
    # Display illumination percentage centered
    illum_x = (128 - len(illumination) * 8) // 2
    display.text(illumination, illum_x, 43, 1)  # Changed from 35 to 43
    
    display.show()

def draw_planet_screen(display, planet_name):
    display.fill(0)
    
    name_x = (128 - len(planet_name) * 8) // 2
    display.text(planet_name, name_x, 5, 1)
    
    data = planet_data[planet_name]
    
    rise_text = "Rise:{}".format(data['rise'])
    set_text = "Set: {}".format(data['set'])
    elev_text = "Elev:{}".format(data['elevation'])
    
    rise_x = (128 - len(rise_text) * 8) // 2
    set_x = (128 - len(set_text) * 8) // 2
    elev_x = (128 - len(elev_text) * 8) // 2
    
    display.text(rise_text, rise_x, 20, 1)
    display.text(set_text, set_x, 32, 1)
    display.text(elev_text, elev_x, 44, 1)
    
    display.show()

# -------------------------
# CALCULATING LMST
# -------------------------

gps_longitude_history = []
lmst_seconds = None

def round_to_2_decimals(value):
    if value is None:
        return None
    return round(value, 2)

def check_gps_stability(current_longitude):
    global gps_longitude_history
    
    if current_longitude is None or current_longitude == 0.0:
        gps_longitude_history = []
        return False
    
    rounded = round_to_2_decimals(current_longitude)
    gps_longitude_history.append(rounded)
    
    if len(gps_longitude_history) > 2:
        gps_longitude_history.pop(0)
    
    if len(gps_longitude_history) == 2:
        if gps_longitude_history[0] == gps_longitude_history[1]:
            return True
    
    return False

def calculate_lmst_initial(longitude_dez, date_str, time_str):
    try:
        date_parts = date_str.split('/')
        if len(date_parts) != 3:
            return None
        day = int(date_parts[0])
        month = int(date_parts[1])
        year = int(date_parts[2])
        
        time_parts = time_str.split(':')
        if len(time_parts) != 3:
            return None
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(float(time_parts[2].split('.')[0])) + 2
        
        if seconds >= 60:
            seconds -= 60
            minutes += 1
        if minutes >= 60:
            minutes -= 60
            hours += 1
        if hours >= 24:
            hours -= 24
        
        longitude_s = longitude_dez/15 * 3600
        
        a = int((14 - month) / 12)
        y = year + 4800 - a
        m = month + 12 * a - 3
        
        jdn = day + int((153 * m + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
        jd_0h = jdn - 0.5
        
        j2000 = 2451545.0
        d = jd_0h - j2000
        T = d / 36525.0
        
        GMST0 = 24110.54841 + 8640184.812866 * T + 0.093104 * T * T - 6.2e-6 * T * T * T
        
        while GMST0 >= 24 * 3600:
            GMST0 -= 24*3600
        
        time_of_day = hours * 3600 + minutes * 60 + seconds
        LMST = GMST0 + longitude_s + 1.00273790935 * time_of_day
        
        while LMST >= 24*3600:
            LMST -= 24*3600
        
        return LMST
    except Exception as e:
        print("LMST error:", e)
        return None

def get_lmst(longitude, date_str, time_str):
    global lmst_seconds
    
    is_stable = check_gps_stability(longitude)
    
    if not is_stable:
        return "---"
    
    if date_str is None or date_str == "" or time_str is None or time_str == "":
        return "---"
    
    lmst_seconds = calculate_lmst_initial(longitude, date_str, time_str)
    
    if lmst_seconds is not None:
        h = int(lmst_seconds/3600)
        m = int((lmst_seconds/3600-h)*60)
        s = int(((lmst_seconds/3600-h)*60 - m)*60)
        
        return "{:02d}:{:02d}:{:02d}".format(h, m, s)
    
    return "---"

# -------------------------
# BUTTON AND LOGGING
# -------------------------

current_log_file = None
current_log_date = None
log_header = """HEADER:

Modules Accuracy /// Latitude: ~ ±2.5 m CEP, Longitude: ~ ±2.5 m CEP, Altitude: ~3–8 m,UTC: 2s delay
(corrected for in code) - time now accurate, LST: ~ 1s delay, Temperature: ±1°C, Humidity: ±3%, Pressure: ± 1 Pa.
To keep the moon illumination accurate, the starting point of calculations needs to be changed for each new moon
and each full moon.

"""

def format_sensor_value(value, unit, decimals=2):
    if value is None:
        return "--- {}".format(unit)
    return "{:.{}f} {}".format(value, decimals, unit)

def write_log_header(f, gps_data, lmst_val):
    f.write("--- START OF OBSERVATION SESSION ---\n")
    f.write("Location:\n")
    f.write("  Latitude: {}\n".format(gps_data.latitude))
    f.write("  Longitude: {}\n".format(gps_data.longitude))
    f.write("  Altitude: {} m\n".format(gps_data.altitude))
    f.write("\n")
    f.write("Date: {}\n".format(gps_data.date))
    f.write("Starting UTC: {}\n".format(gps_data.time))
    f.write("Starting LST: {}\n".format(lmst_val))
    f.write("\n")
    f.write("Sun:\n")
    f.write("  Rise: {}\n".format(sun_rise))
    f.write("  Set: {}\n".format(sun_set))
    f.write("\n")
    f.write("Twilights:\n")
    f.write("  Civil Dawn: {}\n".format(civil_dawn))
    f.write("  Civil Dusk: {}\n".format(civil_dusk))
    f.write("  Nautical Dawn: {}\n".format(nautical_dawn))
    f.write("  Nautical Dusk: {}\n".format(nautical_dusk))
    f.write("  Astronomical Dawn: {}\n".format(astro_dawn))
    f.write("  Astronomical Dusk: {}\n".format(astro_dusk))
    f.write("\n")
    f.write("Moon:\n")
    f.write("  Rise: {}\n".format(moon_rise))
    f.write("  Set: {}\n".format(moon_set))
    f.write("  Phase: {}\n".format(moon_phase))
    f.write("\n")
    f.write("Planets:\n")
    for planet_name in planets_list:
        f.write("  {}:\n".format(planet_name))
        f.write("    Rise: {}\n".format(planet_data[planet_name]['rise']))
        f.write("    Set: {}\n".format(planet_data[planet_name]['set']))
    f.write("\n")
    f.write("=" * 50 + "\n")
    f.write("\n")

def create_log_file(gps_data, lmst_val, moon_val):
    global current_log_file, logging_active, last_log_time, current_log_date
    
    if gps_data.date is None or gps_data.time is None:
        print("No GPS data available")
        return False
    
    try:
        date_parts = gps_data.date.split('/')
        day = date_parts[0]
        month = date_parts[1]
        year = date_parts[2]
        
        time_parts = gps_data.time.split(':')
        hour = time_parts[0]
        minute = time_parts[1]
        second = time_parts[2].split('.')[0]
        
        filename = "{}-{}-{}_{}-{}-{}_UTC.txt".format(day, month, year, hour, minute, second)
        current_log_file = filename
        current_log_date = gps_data.date
        
        with open(filename, 'w') as f:
            f.write(log_header)
            write_log_header(f, gps_data, lmst_val)
            f.write("Time: {}\n".format(gps_data.time))
            f.write("LST: {}\n".format(lmst_val))
            f.write("Temperature: {}\n".format(format_sensor_value(temperature, "C")))
            f.write("Humidity: {}\n".format(format_sensor_value(humidity, "%")))
            f.write("Pressure: {}\n".format(format_sensor_value(pressure_hpa, "hPa")))
            f.write("Dew Point: {}\n".format(format_sensor_value(dew_point, "C")))
            f.write("Moon Illumination: {}\n".format(moon_illumination))
            f.write("Planet Elevations:\n")
            for planet_name in planets_list:
                f.write("  {}: {}°\n".format(planet_name, planet_data[planet_name]['elevation']))
        
        print("Log created:", filename)
        logging_active = True
        last_log_time = time.time()
        return True
        
    except Exception as e:
        print("Error creating log:", e)
        return False

def append_to_log(gps_data, lmst_val, moon_val):
    global current_log_file, current_log_date
    
    if current_log_file is None:
        print("No active log file")
        return False
    
    try:
        if current_log_date != gps_data.date:
            with open(current_log_file, 'a') as f:
                f.write("\n")
                f.write("=" * 50 + "\n")
                f.write("DATE CHANGE - NEW SESSION\n")
                f.write("=" * 50 + "\n")
                f.write("\n")
                write_log_header(f, gps_data, lmst_val)
            current_log_date = gps_data.date
        
        with open(current_log_file, 'a') as f:
            f.write("\n")
            f.write("Time: {}\n".format(gps_data.time))
            f.write("LST: {}\n".format(lmst_val))
            f.write("Temperature: {}\n".format(format_sensor_value(temperature, "C")))
            f.write("Humidity: {}\n".format(format_sensor_value(humidity, "%")))
            f.write("Pressure: {}\n".format(format_sensor_value(pressure_hpa, "hPa")))
            f.write("Dew Point: {}\n".format(format_sensor_value(dew_point, "C")))
            f.write("Planet Elevations:\n")
            for planet_name in planets_list:
                f.write("  {}: {}°\n".format(planet_name, planet_data[planet_name]['elevation']))
        
        print("Data appended to:", current_log_file)
        return True
        
    except Exception as e:
        print("Error appending to log:", e)
        return False

def end_log():
    global logging_active, current_log_file
    
    if current_log_file is None:
        print("No active log to end")
        return False
    
    try:
        with open(current_log_file, 'a') as f:
            f.write("\n")
            f.write("END OF OBSERVATION SESSION\n")
        
        print("Log ended:", current_log_file)
        logging_active = False
        return True
        
    except Exception as e:
        print("Error ending log:", e)
        return False

def check_buttons(gps_data, lmst_val, moon_val, current_scr, prev_vals):
    global last_green, last_red, logging_active, current_screen, last_screen_switch
    
    green_state = white.value()
    red_state = black.value()
    button_pressed = False
    
    if green_state == 0 and last_green == 1:
        time.sleep(debounce)
        if logging_active:
            if end_log():
                oled.fill(0)
                oled.text("End of log!", 25, 28, 1)
                oled.show()
                time.sleep(0.75)
                redraw_screen(gps_data, lmst_val, current_scr, prev_vals)
                button_pressed = True
        else:
            if create_log_file(gps_data, lmst_val, moon_val):
                oled.fill(0)
                oled.text("Logged!", 35, 28, 1)
                oled.show()
                time.sleep(0.75)
                redraw_screen(gps_data, lmst_val, current_scr, prev_vals)
                button_pressed = True
    last_green = green_state
    
    if red_state == 0 and last_red == 1:
        time.sleep(debounce)
        if current_screen == 1:
            current_screen = 2
        elif current_screen == 2:
            current_screen = 3
        elif current_screen == 3:
            current_screen = 4
        elif current_screen == 4:
            current_screen = 5
        elif current_screen == 5:
            current_screen = 6
        elif current_screen == 6:
            current_screen = 7
        elif current_screen == 7:
            current_screen = 8
        elif current_screen == 8:
            current_screen = 9
        elif current_screen == 9:
            current_screen = 10
        elif current_screen == 10:
            current_screen = 11
        elif current_screen == 11:
            current_screen = 12
        elif current_screen == 12:
            current_screen = 13
        elif current_screen == 13:
            current_screen = 14
        elif current_screen == 14:
            current_screen = 15
        elif current_screen == 15:
            current_screen = 16
        elif current_screen == 16:
            current_screen = 17
        elif current_screen == 17:
            current_screen = 1
        else:
            current_screen = 1
        
        last_screen_switch = time.time()
        redraw_screen(gps_data, lmst_val, current_screen, prev_vals)
        button_pressed = True
    last_red = red_state
    
    return button_pressed


def redraw_screen(gps_data, lmst_val, current_scr, prev_vals):
    if current_scr == 9:
        draw_moon_phase(oled, moon_phase)
    elif current_scr == 10:
        draw_moon_illumination(oled, moon_illumination)
    elif current_scr == 8:
        draw_moon_screen(oled, moon_rise, moon_set)
    elif current_scr == 4:
        draw_sun_screen(oled, sun_rise, sun_set)
    elif current_scr == 5:
        draw_twilight_screen(oled, "Civil Twilight", civil_dawn, civil_dusk)
    elif current_scr == 6:
        draw_twilight_screen(oled, "Naut. Twilight", nautical_dawn, nautical_dusk)
    elif current_scr == 7:
        draw_twilight_screen(oled, "Astro. Twilight", astro_dawn, astro_dusk)
    elif current_scr >= 11 and current_scr <= 17:
        planet_index = current_scr - 11
        draw_planet_screen(oled, planets_list[planet_index])
    else:
        if current_scr == 1:
            values = [
                "   Position",
                "",
                "Lat: "  + format_coord(gps_data.latitude, is_latitude=True),
                "Long: " + format_coord(gps_data.longitude, is_latitude=False),
                "Alt: {} m".format(gps_data.altitude),
                ""
            ]
        elif current_scr == 2:
            if gps_data.time is not None:
                time_parts = str(gps_data.time).split(':')
                if len(time_parts) >= 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(float(time_parts[2].split('.')[0])) + 2
                    
                    if seconds >= 60:
                        seconds -= 60
                        minutes += 1
                    if minutes >= 60:
                        minutes -= 60
                        hours += 1
                    if hours >= 24:
                        hours -= 24
                    
                    corrected_time = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
                else:
                    corrected_time = str(gps_data.time).split('.')[0]
            else:
                corrected_time = str(gps_data.time)
            
            values = [
                "  Time & Date",
                "",
                "Date: {}".format(gps_data.date),
                "Time: {}".format(corrected_time),
                "LST: {}".format(lmst_val),
                ""
            ]
        elif current_scr == 3:
            temp_str = format_sensor_value(temperature, "C")
            hum_str = format_sensor_value(humidity, "%")
            press_str = format_sensor_value(pressure_hpa, "hPa", 1)
            dp_str = format_sensor_value(dew_point, "C", 1)
            
            values = [
                "    Ambient",
                "",
                "Temp: {}".format(temp_str),
                "Hum: {}".format(hum_str),
                "Press: {}".format(press_str),
                "Dew Point: {}".format(dp_str)
            ]
        
        oled.fill(0)
        for i, val in enumerate(values):
            oled.text(val, 0, i * 10 + 5)
        oled.show()

# -------------------------
# MAIN LOOP
# -------------------------

prev_values = []

def format_coord(value, is_latitude=True):
    if value is None:
        return "---"
    direction = "N" if (is_latitude and value >= 0) else ""
    direction = "S" if (is_latitude and value < 0) else direction
    direction = "E" if (not is_latitude and value >= 0) else direction
    direction = "W" if (not is_latitude and value < 0) else direction
    return "{:.5f} {}".format(abs(value), direction)

while True:
    read_bme280()
    
    gps_data = gps.get_data()
    
    print(gps_data.has_fix)
    print("Lat: {}  Long: {}  Alt: {} (m) Date: {}  Time: {}".format(gps_data.latitude, gps_data.longitude, gps_data.altitude, gps_data.date, gps_data.time))
    print("Temp: {} C  Humidity: {} %  Pressure: {} hPa".format(temperature, humidity, pressure_hpa))
    
    lmst = get_lmst(gps_data.longitude, gps_data.date, gps_data.time)
    update_moon_phase(gps_data.date, gps_data.time)
    update_sun_times(gps_data)
    update_moon_times(gps_data)
    update_planet_rise_set(gps_data)
    update_planet_elevations(gps_data)
    
    if logging_active:
        current_time = time.time()
        if current_time - last_log_time >= log_interval:
            append_to_log(gps_data, lmst, moon_phase)
            last_log_time = current_time
    
    if time.time() - last_screen_switch >= screen_interval:
        if current_screen == 1:
            current_screen = 2
        elif current_screen == 2:
            current_screen = 3
        elif current_screen == 3:
            current_screen = 4
        elif current_screen == 4:
            current_screen = 5
        elif current_screen == 5:
            current_screen = 6
        elif current_screen == 6:
            current_screen = 7
        elif current_screen == 7:
            current_screen = 8
        elif current_screen == 8:
            current_screen = 9
        elif current_screen == 9:
            current_screen = 10
        elif current_screen == 10:
            current_screen = 11
        elif current_screen == 11:
            current_screen = 12
        elif current_screen == 12:
            current_screen = 13
        elif current_screen == 13:
            current_screen = 14
        elif current_screen == 14:
            current_screen = 15
        elif current_screen == 15:
            current_screen = 16
        elif current_screen == 16:
            current_screen = 17
        elif current_screen == 17:
            current_screen = 1
        else:
            current_screen = 1
        
        if current_screen >= 1 and current_screen <= 3:
            screen_interval = 15
        else:
            screen_interval = 10
            
        last_screen_switch = time.time()
    
    button_was_pressed = False
    for i in range(5):
        if check_buttons(gps_data, lmst, moon_phase, current_screen, prev_values):
            button_was_pressed = True
            break
        time.sleep(0.1)
    
    if not button_was_pressed:
        if current_screen == 1:
            values = [
                "   Position",
                "",
                "Lat: "  + format_coord(gps_data.latitude, is_latitude=True),
                "Long: " + format_coord(gps_data.longitude, is_latitude=False),
                "Alt: {} m".format(gps_data.altitude),
                ""
            ]
        elif current_screen == 2:
            if gps_data.time is not None:
                time_parts = str(gps_data.time).split(':')
                if len(time_parts) >= 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(float(time_parts[2].split('.')[0])) + 2
                    
                    if seconds >= 60:
                        seconds -= 60
                        minutes += 1
                    if minutes >= 60:
                        minutes -= 60
                        hours += 1
                    if hours >= 24:
                        hours -= 24
                    
                    corrected_time = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
                else:
                    corrected_time = str(gps_data.time).split('.')[0]
            else:
                corrected_time = str(gps_data.time)
            
            values = [
                "  Time & Date",
                "",
                "Date: {}".format(gps_data.date),
                "Time: {}".format(corrected_time),
                "LST: {}".format(lmst),
                ""
            ]
        elif current_screen == 3:
            temp_str = format_sensor_value(temperature, "C")
            hum_str = format_sensor_value(humidity, "%")
            press_str = format_sensor_value(pressure_hpa, "hPa", 1)
            dp_str = format_sensor_value(dew_point, "C", 1)
            
            values = [
                "    Ambient",
                "",
                "Temp: {}".format(temp_str),
                "Hum: {}".format(hum_str),
                "Press: {}".format(press_str),
                "Dew Point: {}".format(dp_str)
            ]
        else:
            values = []
        
        if current_screen >= 1 and current_screen <= 3:
            updated = False
            for i, val in enumerate(values):
                if i >= len(prev_values) or val != prev_values[i]:
                    updated = True
                    break
            
            if len(values) != len(prev_values):
                updated = True
            
            prev_values = values[:]
            
            if updated:
                oled.fill(0)
                for i, val in enumerate(values):
                    oled.text(val, 0, i * 10 + 5)
                oled.show()
        
        if current_screen == 4:
            draw_sun_screen(oled, sun_rise, sun_set)
        elif current_screen == 5:
            draw_twilight_screen(oled, "Civil Twilight", civil_dawn, civil_dusk)
        elif current_screen == 6:
            draw_twilight_screen(oled, "Naut. Twilight", nautical_dawn, nautical_dusk)
        elif current_screen == 7:
            draw_twilight_screen(oled, "Astro. Twilight", astro_dawn, astro_dusk)
        elif current_screen == 8:
            draw_moon_screen(oled, moon_rise, moon_set)
        elif current_screen == 9:
            if moon_phase != prev_values[0] if len(prev_values) > 0 else True:
                draw_moon_phase(oled, moon_phase)
                prev_values = [moon_phase]
        elif current_screen == 10:
            draw_moon_illumination(oled, moon_illumination)
        elif current_screen >= 11 and current_screen <= 17:
            planet_index = current_screen - 11
            draw_planet_screen(oled, planets_list[planet_index])
    
    for i in range(5):
        check_buttons(gps_data, lmst, moon_phase, current_screen, prev_values)
        time.sleep(0.1)
