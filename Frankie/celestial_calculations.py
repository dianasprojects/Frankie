import math

OBJECT_NAMES = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

OBJECT_DATA = [
    [0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081],
    [0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418],
    [1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0, 0],
    [1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343],
    [5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106],
    [9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794],
    [19.1891646, -0.00196176, 0.04725744, -0.00004397, 0.77263783, -0.00242939, 313.23810451, 428.48202785, 170.95427630, 0.40805281, 74.01692503, 0.04240589],
    [30.06992276, 0.00026291, 0.00859048, 0.00005105, 1.77004347, 0.00035372, -55.12002969, 218.45945325, 44.96476227, -0.32241464, 131.78422574, -0.00508664],
]

RAD = math.pi / 180.0
DEG = 180.0 / math.pi
ECLIPTIC_ANGLE = 23.43928

class PlanetCalculator:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.x_coord = 0.0
        self.y_coord = 0.0
        self.z_coord = 0.0
        self.x_earth = 0.0
        self.y_earth = 0.0
        self.z_earth = 0.0
        
    def get_julian_date(self, day, month, year, hour, minute, seconds):
        if month <= 2:
            year -= 1
            month += 12
            
        A = int(year / 100)
        B = int(A / 4)
        C = 2 - A + B
        E = int(365.25 * (year + 4716))
        F = int(30.6001 * (month + 1))
        
        jd = C + day + E + F - 1524.5
        jd_frac = (hour / 24.0) + (minute / 1440.0) + (seconds / 86400.0)
        
        return jd + jd_frac
    
    def format_angle_deg(self, deg):
        if deg >= 360 or deg < 0:
            if deg < 0:
                while deg < 0:
                    deg += 360
            x = int(deg)
            comma = deg - x
            y = x % 360
            return comma + y
        return deg
    
    def calc_eccentric_anomaly(self, mean_anomaly, eccentricity):
        mean_anomaly_rad = mean_anomaly * RAD
        
        eccentric_anomaly = mean_anomaly_rad + (eccentricity * math.sin(mean_anomaly_rad))
        delta = 1.0
        iterations = 0
        
        while abs(delta) > 0.000001 and iterations < 20:
            delta = (mean_anomaly_rad - eccentric_anomaly + 
                    (eccentricity * math.sin(eccentric_anomaly))) / \
                    (1.0 - eccentricity * math.cos(eccentric_anomaly))
            eccentric_anomaly += delta
            iterations += 1
            
        return eccentric_anomaly * DEG
    
    def calc_orbital_coordinates(self, semi_major_axis, eccentricity, eccentric_anomaly):
        eccentric_anomaly_rad = eccentric_anomaly * RAD
        
        true_anomaly = 2.0 * math.atan(
            math.sqrt((1.0 + eccentricity) / (1.0 - eccentricity)) * 
            math.tan(eccentric_anomaly_rad / 2.0)
        )
        true_anomaly = self.format_angle_deg(true_anomaly * DEG)
        
        radius = semi_major_axis * (1.0 - (eccentricity * math.cos(eccentric_anomaly_rad)))
        
        y_rad = true_anomaly * RAD
        self.x_coord = radius * math.cos(0.0) * math.cos(y_rad)
        self.y_coord = radius * math.cos(0.0) * math.sin(y_rad)
        self.z_coord = radius * math.sin(0.0)
    
    def rot_x(self, alpha):
        alpha_rad = alpha * RAD
        y = math.cos(alpha_rad) * self.y_coord - math.sin(alpha_rad) * self.z_coord
        z = math.sin(alpha_rad) * self.y_coord + math.cos(alpha_rad) * self.z_coord
        self.y_coord = y
        self.z_coord = z
    
    def rot_z(self, alpha):
        alpha_rad = alpha * RAD
        x = math.cos(alpha_rad) * self.x_coord - math.sin(alpha_rad) * self.y_coord
        y = math.sin(alpha_rad) * self.x_coord + math.cos(alpha_rad) * self.y_coord
        self.x_coord = x
        self.y_coord = y
    
    def calc_vector_subtract(self, xe, xo, ye, yo, ze, zo):
        self.x_coord = xo - xe
        self.y_coord = yo - ye
        self.z_coord = zo - ze
    
    def calc_ra_dec(self):
        ra = math.atan2(self.y_coord, self.x_coord) * DEG
        ra = self.format_angle_deg(ra)
        
        dec = math.atan2(self.z_coord, math.sqrt(self.x_coord**2 + self.y_coord**2)) * DEG
        dec = self.format_angle_deg(dec)
        if dec > 90:
            dec -= 360
        
        return ra, dec
    
    def jd_to_gmst(self, JD):
        D = JD - 2451545.0
        GMST = 280.46061837 + 360.98564736629 * D
        return GMST % 360
    
    def calc_lst(self, JD):
        GMST = self.jd_to_gmst(JD)
        LST = (GMST + self.lon) % 360
        return LST
    
    def wrap180(self, deg):
        return (deg + 180) % 360 - 180
    
    def calc_altitude(self, ra_deg, dec_deg, lst_deg):
        H_deg = self.wrap180(lst_deg - ra_deg)
    
        H_rad = H_deg * RAD
        dec_rad = dec_deg * RAD
        lat_rad = self.lat * RAD
    
        sin_h = (math.sin(lat_rad) * math.sin(dec_rad) + 
             math.cos(lat_rad) * math.cos(dec_rad) * math.cos(H_rad))
        h_deg = math.asin(sin_h) * DEG
    
    
        return h_deg
    
    def get_object_position(self, object_number, jd):
        T = (jd - 2451545.0) / 36525.0
        
        data = OBJECT_DATA[object_number]
        
        semi_major_axis = data[0] + (T * data[1])
        eccentricity = data[2] + (T * data[3])
        inclination = self.format_angle_deg(data[4] + (T * data[5]))
        mean_longitude = self.format_angle_deg(data[6] + (T * data[7]))
        longitude_perihelion = self.format_angle_deg(data[8] + (T * data[9]))
        longitude_ascending_node = self.format_angle_deg(data[10] + (T * data[11]))
        
        mean_anomaly = self.format_angle_deg(mean_longitude - longitude_perihelion)
        argument_perihelion = self.format_angle_deg(longitude_perihelion - longitude_ascending_node)
        
        eccentric_anomaly = self.calc_eccentric_anomaly(mean_anomaly, eccentricity)
        
        self.calc_orbital_coordinates(semi_major_axis, eccentricity, eccentric_anomaly)
        
        self.rot_z(argument_perihelion)
        self.rot_x(inclination)
        self.rot_z(longitude_ascending_node)
    
    def calculate_sun_ra_dec(self, day, month, year, hour=0, minute=0, seconds=0):
        jd = self.get_julian_date(day, month, year, hour, minute, seconds)
        d = jd - 2451545.0
        
        w = self.format_angle_deg(282.9404 + 4.70935E-5 * d)
        e = 0.016709 - 1.151E-9 * d
        M = self.format_angle_deg(356.0470 + 0.9856002585 * d)
        
        E = self.calc_eccentric_anomaly(M, e)
        
        E_rad = E * RAD
        xv = math.cos(E_rad) - e
        yv = math.sin(E_rad) * math.sqrt(1.0 - e*e)
        v = math.atan2(yv, xv) * DEG
        
        lon_sun = self.format_angle_deg(v + w)
        
        ecl = 23.4393 - 3.563E-7 * d
        x = math.cos(lon_sun * RAD)
        y = math.sin(lon_sun * RAD)
        
        xe = x
        ye = y * math.cos(ecl * RAD)
        ze = y * math.sin(ecl * RAD)
        
        ra = math.atan2(ye, xe) * DEG
        ra = self.format_angle_deg(ra)
        dec = math.atan2(ze, math.sqrt(xe*xe + ye*ye)) * DEG
        
        return ra, dec
    
    def calculate_sun_rise_set(self, day, month, year, h_horizon=-0.833):
        ra, dec = self.calculate_sun_ra_dec(day, month, year, 12, 0, 0)
        
        lat_rad = self.lat * RAD
        dec_rad = dec * RAD
        h_rad = h_horizon * RAD
        
        cos_LHA = (math.sin(h_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / \
                  (math.cos(lat_rad) * math.cos(dec_rad))
        
        if cos_LHA < -1.0:
            return {'rise': None, 'set': None, 'status': 'always_above'}
        elif cos_LHA > 1.0:
            return {'rise': None, 'set': None, 'status': 'always_below'}
        
        LHA = math.acos(cos_LHA) * DEG
        
        jd_noon = self.get_julian_date(day, month, year, 12, 0, 0)
        d = jd_noon - 2451545.0
        w = self.format_angle_deg(282.9404 + 4.70935E-5 * d)
        M = self.format_angle_deg(356.0470 + 0.9856002585 * d)
        L = self.format_angle_deg(M + w)
        GMST0 = self.format_angle_deg(L + 180)
        
        UT_south = (ra - GMST0 - self.lon) / 15.0
        while UT_south < 0:
            UT_south += 24
        while UT_south >= 24:
            UT_south -= 24
        
        LHA_hours = LHA / 15.0
        
        rise_UT = UT_south - LHA_hours
        set_UT = UT_south + LHA_hours
        
        def format_time(ut):
            while ut < 0:
                ut += 24
            while ut >= 24:
                ut -= 24
            hours = int(ut)
            minutes = int((ut - hours) * 60)
            return "{:02d}:{:02d}".format(hours, minutes)
        
        return {
            'rise': format_time(rise_UT),
            'set': format_time(set_UT),
            'status': 'normal'
        }
    
    def calculate_twilight_times(self, day, month, year):
        results = {}
        
        sun_times = self.calculate_sun_rise_set(day, month, year, h_horizon=-0.833)
        results['sunrise'] = sun_times
        
        civil = self.calculate_sun_rise_set(day, month, year, h_horizon=-6.0)
        results['civil_dawn'] = civil
        
        nautical = self.calculate_sun_rise_set(day, month, year, h_horizon=-12.0)
        results['nautical_dawn'] = nautical
        
        astronomical = self.calculate_sun_rise_set(day, month, year, h_horizon=-18.0)
        results['astronomical_dawn'] = astronomical
        
        return results
    
    def moon_position_vf(self, day_offset):
        l = 0.606434 + 0.03660110129 * day_offset
        m = 0.374897 + 0.03629164709 * day_offset
        f = 0.259091 + 0.03674819520 * day_offset
        d = 0.827362 + 0.03386319198 * day_offset
        n = 0.347343 - 0.00014709391 * day_offset
        g = 0.993126 + 0.00273777850 * day_offset
        
        l = 2.0 * math.pi * (l - math.floor(l))
        m = 2.0 * math.pi * (m - math.floor(m))
        f = 2.0 * math.pi * (f - math.floor(f))
        d = 2.0 * math.pi * (d - math.floor(d))
        n = 2.0 * math.pi * (n - math.floor(n))
        g = 2.0 * math.pi * (g - math.floor(g))
        
        v = (0.39558 * math.sin(f + n) +
             0.08200 * math.sin(f) +
             0.03257 * math.sin(m - f - n) +
             0.01092 * math.sin(m + f + n) +
             0.00666 * math.sin(m - f) -
             0.00644 * math.sin(m + f - 2.0*d + n) -
             0.00331 * math.sin(f - 2.0*d + n) -
             0.00304 * math.sin(f - 2.0*d) -
             0.00240 * math.sin(m - f - 2.0*d - n) +
             0.00226 * math.sin(m + f) -
             0.00108 * math.sin(m + f - 2.0*d) -
             0.00079 * math.sin(f - n) +
             0.00078 * math.sin(f + 2.0*d + n))
        
        u = (1.0 -
             0.10828 * math.cos(m) -
             0.01880 * math.cos(m - 2.0*d) -
             0.01479 * math.cos(2.0*d) +
             0.00181 * math.cos(2.0*m - 2.0*d) -
             0.00147 * math.cos(2.0*m) -
             0.00105 * math.cos(2.0*d - g) -
             0.00075 * math.cos(m - 2.0*d + g))
        
        w = (0.10478 * math.sin(m) -
             0.04105 * math.sin(2.0*f + 2.0*n) -
             0.02130 * math.sin(m - 2.0*d) -
             0.01779 * math.sin(2.0*f + n) +
             0.01774 * math.sin(n) +
             0.00987 * math.sin(2.0*d) -
             0.00338 * math.sin(m - 2.0*f - 2.0*n) -
             0.00309 * math.sin(g) -
             0.00190 * math.sin(2.0*f) -
             0.00144 * math.sin(m + n) -
             0.00144 * math.sin(m - 2.0*f - n) -
             0.00113 * math.sin(m + 2.0*f + 2.0*n) -
             0.00094 * math.sin(m - 2.0*d + g) -
             0.00092 * math.sin(2.0*m - 2.0*d))
        
        s = w / math.sqrt(u - v*v)
        ra = l + math.atan(s / math.sqrt(1.0 - s*s))
        
        s = v / math.sqrt(u)
        dec = math.atan(s / math.sqrt(1.0 - s*s))
        
        distance = 60.40974 * math.sqrt(u)
        
        return ra, dec, distance
    
    def interpolate_3point(self, f0, f1, f2, p):
        a = f1 - f0
        b = f2 - f1 - a
        return f0 + p * (2.0*a + b * (2.0*p - 1.0))
    
    def local_sidereal_time_deg(self, day_offset, longitude):
        lst = (15.0 * (6.697374558 + 0.06570982441908 * day_offset +
                       (day_offset % 1.0) * 24.0 + 12.0 +
                       0.000026 * (day_offset / 36525.0) * (day_offset / 36525.0)) +
               longitude) / 360.0
        lst = (lst - math.floor(lst)) * 360.0
        return lst
    
    def calculate_moon_rise_set(self, day, month, year, search_window=48):
        jd = self.get_julian_date(day, month, year, 12, 0, 0)
        offset_days = jd - 2451545.0
        
        search_start_offset = offset_days - float(search_window) / (2.0 * 24.0)
        
        moon_pos = []
        for i in range(3):
            ra, dec, dist = self.moon_position_vf(search_start_offset + float(i) * float(search_window) / (2.0 * 24.0))
            moon_pos.append({'ra': ra, 'dec': dec, 'dist': dist})
        
        if moon_pos[1]['ra'] <= moon_pos[0]['ra']:
            moon_pos[1]['ra'] += 2.0 * math.pi
        if moon_pos[2]['ra'] <= moon_pos[1]['ra']:
            moon_pos[2]['ra'] += 2.0 * math.pi
        
        K1 = 15.0 * (math.pi / 180.0) * 1.0027379
        
        has_rise = False
        has_set = False
        rise_time_hours = None
        set_time_hours = None
        
        mp_window = [
            {'ra': moon_pos[0]['ra'], 'dec': moon_pos[0]['dec'], 'dist': moon_pos[0]['dist']},
            {'ra': 0.0, 'dec': 0.0, 'dist': 0.0},
            {'ra': 0.0, 'dec': 0.0, 'dist': 0.0}
        ]
        
        for k in range(search_window):
            ph = float(k + 1) / float(search_window)
            
            mp_window[2]['ra'] = self.interpolate_3point(moon_pos[0]['ra'], moon_pos[1]['ra'], moon_pos[2]['ra'], ph)
            mp_window[2]['dec'] = self.interpolate_3point(moon_pos[0]['dec'], moon_pos[1]['dec'], moon_pos[2]['dec'], ph)
            mp_window[2]['dist'] = moon_pos[2]['dist']
            
            lst_rad = self.local_sidereal_time_deg(search_start_offset, self.lon) * (math.pi / 180.0)
            
            ha = [0.0, 0.0, 0.0]
            ha[0] = lst_rad - mp_window[0]['ra'] + float(k) * K1
            ha[2] = lst_rad - mp_window[2]['ra'] + float(k) * K1 + K1
            ha[1] = (ha[2] + ha[0]) / 2.0
            
            mp_window[1]['dec'] = (mp_window[2]['dec'] + mp_window[0]['dec']) / 2.0
            
            s = math.sin(self.lat * RAD)
            c = math.cos(self.lat * RAD)
            
            z = math.cos((math.pi / 180.0) * (90.567 - 41.685 / mp_window[0]['dist']))
            
            VHz = [0.0, 0.0, 0.0]
            VHz[0] = s * math.sin(mp_window[0]['dec']) + c * math.cos(mp_window[0]['dec']) * math.cos(ha[0]) - z
            VHz[2] = s * math.sin(mp_window[2]['dec']) + c * math.cos(mp_window[2]['dec']) * math.cos(ha[2]) - z
            
            if (VHz[0] < 0 and VHz[2] < 0) or (VHz[0] > 0 and VHz[2] > 0):
                mp_window[0] = mp_window[2]
                continue
            
            VHz[1] = s * math.sin(mp_window[1]['dec']) + c * math.cos(mp_window[1]['dec']) * math.cos(ha[1]) - z
            
            a = 2.0 * VHz[2] - 4.0 * VHz[1] + 2.0 * VHz[0]
            b = 4.0 * VHz[1] - 3.0 * VHz[0] - VHz[2]
            dd = b * b - 4.0 * a * VHz[0]
            
            if dd < 0:
                mp_window[0] = mp_window[2]
                continue
            
            dd = math.sqrt(dd)
            e = (-b + dd) / (2.0 * a)
            if e < 0 or e > 1.0:
                e = (-b - dd) / (2.0 * a)
            
            time_hours = float(k) + e + 1.0/120.0
            
            if VHz[0] < 0 and VHz[2] > 0:
                if not has_rise or abs(time_hours - float(search_window)/2.0) < abs(rise_time_hours - float(search_window)/2.0):
                    rise_time_hours = time_hours
                    has_rise = True
            elif VHz[0] > 0 and VHz[2] < 0:
                if not has_set or abs(time_hours - float(search_window)/2.0) < abs(set_time_hours - float(search_window)/2.0):
                    set_time_hours = time_hours
                    has_set = True
            
            mp_window[0] = mp_window[2]
        
        def format_event_time(time_hours):
            if time_hours is None:
                return None
            
            # Calculate time directly without JD conversion
            # time_hours is hours from search_start_offset
            # search_start_offset is at (day, month, year, 12, 0, 0) minus 24 hours
            # So time_hours=0 corresponds to (day-1, month, year, 12:00)
            # We want the actual UTC time
            
            # Start time is noon minus 24 hours = previous day noon
            start_hour = 12.0 - 24.0  # = -12, which wraps to previous day
            actual_hour = start_hour + time_hours
            
            # Normalize to 0-24 range
            while actual_hour < 0.0:
                actual_hour += 24.0
            while actual_hour >= 24.0:
                actual_hour -= 24.0
            
            hh = int(actual_hour)
            mm = int((actual_hour - float(hh)) * 60.0)
            
            return "{:02d}:{:02d}".format(hh, mm)
        
        if not has_rise and not has_set:
            return {'rise': None, 'set': None, 'status': 'no_event'}
        
        return {
            'rise': format_event_time(rise_time_hours) if has_rise else None,
            'set': format_event_time(set_time_hours) if has_set else None,
            'status': 'normal'
        }
    
    def calculate_planet(self, planet_name, day, month, year, hour=0, minute=0, seconds=0):
        jd = self.get_julian_date(day, month, year, hour, minute, seconds)
    
        self.get_object_position(2, jd)
        self.x_earth = self.x_coord
        self.y_earth = self.y_coord
        self.z_earth = self.z_coord
    
        try:
            planet_idx = OBJECT_NAMES.index(planet_name)
        except ValueError:
            return None
    
        if planet_idx == 2:
            return None
    
        self.get_object_position(planet_idx, jd)
    
        self.calc_vector_subtract(self.x_earth, self.x_coord,
                             self.y_earth, self.y_coord,
                             self.z_earth, self.z_coord)
    
        self.rot_x(ECLIPTIC_ANGLE)
    
        ra, dec = self.calc_ra_dec()
    
    # Return only RA and Dec - altitude calculated separately with accurate LST
        return {
            'planet': planet_name,
            'ra': ra,
            'dec': dec
        }
    
    def calculate_planet_ra_dec(self, planet_name, day, month, year, hour=0, minute=0, seconds=0):
        jd = self.get_julian_date(day, month, year, hour, minute, seconds)
        
        self.get_object_position(2, jd)
        self.x_earth = self.x_coord
        self.y_earth = self.y_coord
        self.z_earth = self.z_coord
        
        try:
            planet_idx = OBJECT_NAMES.index(planet_name)
        except ValueError:
            return None
        
        if planet_idx == 2:
            return None
        
        self.get_object_position(planet_idx, jd)
        
        self.calc_vector_subtract(self.x_earth, self.x_coord,
                                 self.y_earth, self.y_coord,
                                 self.z_earth, self.z_coord)
        
        self.rot_x(ECLIPTIC_ANGLE)
        
        ra, dec = self.calc_ra_dec()
        
        return ra, dec
    
    def calculate_planet_rise_set(self, planet_name, day, month, year, h_horizon=-0.5667, iterations=3):
        def constrain(v):
            if v < 0:
                return v + 1.0
            if v > 1.0:
                return v - 1.0
            return v
        
        def time_to_hms(hours):
            h = int(hours)
            m = int((hours - float(h)) * 60.0)
            s = int(((hours - float(h)) * 60.0 - float(m)) * 60.0)
            return h, m, s
        
        result = self.calculate_planet_ra_dec(planet_name, day, month, year, 0, 0, 0)
        if not result:
            return None
        
        ra, dec = result
        
        jd = self.get_julian_date(day, month, year, 0, 0, 0)
        gmst = self.jd_to_gmst(jd)
        
        lon_meeus = -self.lon
        
        lat_rad = self.lat * RAD
        dec_rad = dec * RAD
        h0_rad = h_horizon * RAD
        
        cos_H0 = (math.sin(h0_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / \
                 (math.cos(lat_rad) * math.cos(dec_rad))
        
        if cos_H0 < -1.0:
            transit = (ra + lon_meeus - gmst) / 360.0
            transit = constrain(transit) * 24.0
            h_transit, m_transit, s_transit = time_to_hms(transit)
            result_transit = self.calculate_planet_ra_dec(planet_name, day, month, year, h_transit, m_transit, s_transit)
            if result_transit:
                ra_transit, dec_transit = result_transit
                transit = constrain((ra_transit + lon_meeus - gmst) / 360.0) * 24.0
            h, m, s = time_to_hms(transit)
            return {'rise': '-', 'transit': "{:02d}:{:02d}".format(h, m), 'set': '-', 'status': 'always_above'}
        elif cos_H0 > 1.0:
            return {'rise': '-', 'transit': '-', 'set': '-', 'status': 'always_below'}
        
        H0 = math.acos(cos_H0) * DEG
        
        transit = (ra + lon_meeus - gmst) / 360.0
        rise = transit - (H0 / 360.0)
        set_time = transit + (H0 / 360.0)
        
        transit = constrain(transit) * 24.0
        rise = constrain(rise) * 24.0
        set_time = constrain(set_time) * 24.0
        
        for i in range(iterations):
            h_rise, m_rise, s_rise = time_to_hms(rise)
            result_rise = self.calculate_planet_ra_dec(planet_name, day, month, year, h_rise, m_rise, s_rise)
            if result_rise:
                ra_rise, dec_rise = result_rise
                dec_rad = dec_rise * RAD
                cos_H0 = (math.sin(h0_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / \
                         (math.cos(lat_rad) * math.cos(dec_rad))
                if -1.0 <= cos_H0 <= 1.0:
                    H0 = math.acos(cos_H0) * DEG
                    transit_new = (ra_rise + lon_meeus - gmst) / 360.0
                    rise = constrain(transit_new - (H0 / 360.0)) * 24.0
            
            h_transit, m_transit, s_transit = time_to_hms(transit)
            result_transit = self.calculate_planet_ra_dec(planet_name, day, month, year, h_transit, m_transit, s_transit)
            if result_transit:
                ra_transit, dec_transit = result_transit
                transit = constrain((ra_transit + lon_meeus - gmst) / 360.0) * 24.0
            
            h_set, m_set, s_set = time_to_hms(set_time)
            result_set = self.calculate_planet_ra_dec(planet_name, day, month, year, h_set, m_set, s_set)
            if result_set:
                ra_set, dec_set = result_set
                dec_rad = dec_set * RAD
                cos_H0 = (math.sin(h0_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / \
                         (math.cos(lat_rad) * math.cos(dec_rad))
                if -1.0 <= cos_H0 <= 1.0:
                    H0 = math.acos(cos_H0) * DEG
                    transit_new = (ra_set + lon_meeus - gmst) / 360.0
                    set_time = constrain(transit_new + (H0 / 360.0)) * 24.0
        
        def format_time(hours):
            h, m, s = time_to_hms(hours)
            return "{:02d}:{:02d}".format(h, m)
        
        return {
            'rise': format_time(rise),
            'transit': format_time(transit),
            'set': format_time(set_time),
            'status': 'normal'
        }




