"""
ref.py — a faithful Python transcription of the app's Kotlin astronomy.

Why this exists: there is no JDK in this sandbox, so the only way to know whether
PrayerCalculator is right is to run the same formulas somewhere else and diff them
against an independent reference (the Aladhan API). Line-for-line port of
Astronomy.kt + PrayerCalculator.forDate, so a disagreement here is a disagreement
in the app.
"""
import math
from datetime import date, datetime, timedelta, timezone

D = math.radians
R = math.degrees


def unwind(a):
    return a - 360.0 * math.floor(a / 360.0)


def normalize(a, b):
    return a - b * math.floor(a / b)


def closest_angle(a):
    return a - 360.0 * math.floor((a + 180.0) / 360.0)


def julian_day(y, m, d, hours=0.0):
    yy = y if m > 2 else y - 1
    mm = m if m > 2 else m + 12
    dd = d + hours / 24.0
    a = math.floor(yy / 100.0)
    b = math.floor(2.0 - a + a / 4.0)
    return math.floor(365.25 * (yy + 4716)) + math.floor(30.6001 * (mm + 1)) + dd + b - 1524.5


def julian_century(jd):
    return (jd - 2451545.0) / 36525.0


def mean_solar_longitude(t):
    return unwind(280.4664567 + 36000.76983 * t + 0.0003032 * t * t)


def mean_lunar_longitude(t):
    return unwind(218.3165 + 481267.8813 * t)


def ascending_lunar_node(t):
    return unwind(125.04452 - 1934.136261 * t + 0.0020708 * t * t + t ** 3 / 450000.0)


def mean_solar_anomaly(t):
    return unwind(357.52911 + 35999.05029 * t - 0.0001537 * t * t)


def solar_equation_of_center(t, m):
    mr = D(m)
    t1 = (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
    t2 = (0.019993 - 0.000101 * t) * math.sin(2 * mr)
    t3 = 0.000289 * math.sin(3 * mr)
    return t1 + t2 + t3


def apparent_solar_longitude(t, l0):
    lon = l0 + solar_equation_of_center(t, mean_solar_anomaly(t))
    o = 125.04 - 1934.136 * t
    return unwind(lon - 0.00569 - 0.00478 * math.sin(D(o)))


def mean_sidereal_time(t):
    jd = t * 36525.0 + 2451545.0
    theta = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
             + 0.000387933 * t * t - t ** 3 / 38710000.0)
    return unwind(theta)


def nutation_in_longitude(l0, lp, o):
    t1 = (-17.2 / 3600.0) * math.sin(D(o))
    t2 = (1.32 / 3600.0) * math.sin(2 * D(l0))
    t3 = (0.23 / 3600.0) * math.sin(2 * D(lp))
    t4 = (0.21 / 3600.0) * math.sin(2 * D(o))
    return t1 - t2 - t3 + t4


def nutation_in_obliquity(l0, lp, o):
    t1 = (9.2 / 3600.0) * math.cos(D(o))
    t2 = (0.57 / 3600.0) * math.cos(2 * D(l0))
    t3 = (0.10 / 3600.0) * math.cos(2 * D(lp))
    t4 = (0.09 / 3600.0) * math.cos(2 * D(o))
    return t1 + t2 + t3 - t4


def mean_obliquity(t):
    return 23.439291 - 0.013004167 * t - 0.0000001639 * t * t + 0.0000005036 * t ** 3


def apparent_obliquity(t, e0):
    return e0 + 0.00256 * math.cos(D(125.04 - 1934.136 * t))


class SolarCoordinates:
    def __init__(self, jd):
        t = julian_century(jd)
        l0 = mean_solar_longitude(t)
        lp = mean_lunar_longitude(t)
        o = ascending_lunar_node(t)
        lam = D(apparent_solar_longitude(t, l0))
        theta0 = mean_sidereal_time(t)
        dpsi = nutation_in_longitude(l0, lp, o)
        deps = nutation_in_obliquity(l0, lp, o)
        e0 = mean_obliquity(t)
        eapp = D(apparent_obliquity(t, e0))
        self.declination = R(math.asin(math.sin(eapp) * math.sin(lam)))
        self.right_ascension = unwind(R(math.atan2(math.cos(eapp) * math.sin(lam), math.cos(lam))))
        self.apparent_sidereal_time = theta0 + (dpsi * 3600.0 * math.cos(D(e0 + deps))) / 3600.0


def interpolate(y2, y1, y3, n):
    a = y2 - y1
    b = y3 - y2
    c = b - a
    return y2 + (n / 2.0) * (a + b + n * c)


def interpolate_angles(y2, y1, y3, n):
    a = unwind(y2 - y1)
    b = unwind(y3 - y2)
    c = b - a
    return y2 + (n / 2.0) * (a + b + n * c)


def approximate_transit(longitude, theta0, ra):
    lw = -longitude
    return normalize((ra + lw - theta0) / 360.0, 1.0)


def corrected_transit(m0, longitude, theta0, ra2, ra1, ra3):
    lw = -longitude
    theta = unwind(theta0 + 360.985647 * m0)
    ra = unwind(interpolate_angles(ra2, ra1, ra3, m0))
    h = closest_angle(theta - lw - ra)
    dm = h / -360.0
    return (m0 + dm) * 24.0


def corrected_hour_angle(m0, angle, latitude, longitude, after, theta0, ra2, ra1, ra3, d2, d1, d3):
    lw = -longitude
    term1 = math.sin(D(angle)) - math.sin(D(latitude)) * math.sin(D(d2))
    term2 = math.cos(D(latitude)) * math.cos(D(d2))
    ratio = term1 / term2
    if ratio > 1.0 or ratio < -1.0:
        return float("nan")
    h0 = R(math.acos(ratio))
    m = m0 + h0 / 360.0 if after else m0 - h0 / 360.0
    theta = unwind(theta0 + 360.985647 * m)
    ra = unwind(interpolate_angles(ra2, ra1, ra3, m))
    decl = interpolate(d2, d1, d3, m)
    h = theta - lw - ra
    altitude = R(math.asin(math.sin(D(latitude)) * math.sin(D(decl))
                           + math.cos(D(latitude)) * math.cos(D(decl)) * math.cos(D(h))))
    denom = 360.0 * math.cos(D(decl)) * math.cos(D(latitude)) * math.sin(D(h))
    if abs(denom) < 1e-12:
        return float("nan")
    return (m + (altitude - angle) / denom) * 24.0


def asr_angle(latitude, declination, shadow_factor):
    tangent = abs(latitude - declination)
    inverse = shadow_factor + math.tan(D(tangent))
    return R(math.atan(1.0 / inverse))


# (fajr angle, isha angle, isha interval min, isha Ramadan interval min, dhuhr adjust min)
METHODS = {
    "KARACHI": (18.0, 18.0, 0, 0, 1),
    "MWL": (18.0, 17.0, 0, 0, 1),
    "ISNA": (15.0, 15.0, 0, 0, 1),
    "EGYPTIAN": (19.5, 17.5, 0, 0, 1),
    "UMM_AL_QURA": (18.5, 0.0, 90, 120, 1),
    "DUBAI": (18.2, 18.2, 0, 0, 1),
    "KUWAIT": (18.0, 17.5, 0, 0, 1),
    "QATAR": (18.0, 0.0, 90, 120, 1),
    "SINGAPORE": (20.0, 18.0, 0, 0, 1),
}
SHADOW = {"SHAFI": 1.0, "HANAFI": 2.0}

HIJRI_MONTHS = ["Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
                "Jumada al-Ula", "Jumada al-Akhirah", "Rajab", "Sha'ban",
                "Ramadan", "Shawwal", "Dhu al-Qadah", "Dhu al-Hijjah"]


def hijri_from_gregorian(y, m, d):
    """Arithmetic (Kuwaiti) Hijri date. Mirrors HijriCalendar.kt exactly."""
    jd = int(julian_day(y, m, d) + 0.5)
    l0 = jd - 1948440 + 10632
    n = (l0 - 1) // 10631
    l = l0 - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    month = (24 * l) // 709
    day = l - (709 * month) // 24
    year = 30 * n + j - 30
    return year, month, day


def prayer_times_hours(y, m, d, lat, lon, method="KARACHI", madhab="SHAFI"):
    """Returns dict prayer -> UT decimal hours, exactly as PrayerCalculator does."""
    fajr_angle, isha_angle, isha_interval, isha_ramadan, dhuhr_adj = METHODS[method]
    hy, hm, hd = hijri_from_gregorian(y, m, d)
    is_ramadan = hm == 9
    shadow = SHADOW[madhab]
    jd = julian_day(y, m, d)
    prev, cur, nxt = SolarCoordinates(jd - 1), SolarCoordinates(jd), SolarCoordinates(jd + 1)
    m0 = approximate_transit(lon, cur.apparent_sidereal_time, cur.right_ascension)

    def ha(angle, after):
        return corrected_hour_angle(m0, angle, lat, lon, after, cur.apparent_sidereal_time,
                                    cur.right_ascension, prev.right_ascension, nxt.right_ascension,
                                    cur.declination, prev.declination, nxt.declination)

    transit = corrected_transit(m0, lon, cur.apparent_sidereal_time,
                                cur.right_ascension, prev.right_ascension, nxt.right_ascension)
    sunrise = ha(-50.0 / 60.0, False)
    sunset = ha(-50.0 / 60.0, True)
    night = (sunrise + 24.0) - sunset

    # High-latitude fallbacks are NOT wrapped into [0,24): these are hours from
    # midnight UT of `date`, and Fajr in India is legitimately negative.
    raw_fajr = ha(-fajr_angle, False)
    fajr = raw_fajr if not math.isnan(raw_fajr) else (sunrise - night / 2.0)

    interval = isha_ramadan if (isha_ramadan > 0 and is_ramadan) else isha_interval
    if interval > 0:
        isha = sunset + interval / 60.0
    else:
        raw_isha = ha(-isha_angle, True)
        isha = raw_isha if not math.isnan(raw_isha) else (sunset + night / 2.0)

    aa = asr_angle(lat, cur.declination, shadow)
    asr = ha(aa, True)
    if math.isnan(asr):
        asr = transit + 3.5

    return {
        "FAJR": fajr, "SUNRISE": sunrise,
        "DHUHR": transit + dhuhr_adj / 60.0,
        "ASR": asr, "MAGHRIB": sunset, "ISHA": isha,
    }, {"transit_ut": transit, "sunrise": sunrise, "sunset": sunset,
        "decl": cur.declination, "hijri": (hy, hm, hd), "is_ramadan": is_ramadan,
        "imsak": fajr - 10.0 / 60.0, "midnight": sunset + night / 2.0,
        "last_third": sunset + night * 2.0 / 3.0, "night_minutes": round(night * 60.0)}


def round_seconds(total_hours):
    """Local decimal hours -> seconds since local midnight, rounded once.

    This is exactly what the Kotlin does: round to the nearest second, then
    display the minute that second falls in. Rounding up to the next minute here
    would add a second offset on top of Dhuhr's one-minute guard and push it late,
    which is the bug this function is written not to have.
    """
    return int(round(total_hours * 3600.0))


def to_local(date_tuple, ut_hours, tz_offset_hours):
    """UT decimal hours -> local HH:MM, rounded the way the app does it."""
    secs = round_seconds(ut_hours + tz_offset_hours)
    # nearest minute, once: truncating to the minute would round every time DOWN
    mins_total = int(math.floor(secs / 60.0 + 0.5)) % 1440
    h, m = divmod(mins_total, 60)
    return f"{h:02d}:{m:02d}"


if __name__ == "__main__":
    # IST = +5.5. Compare to Aladhan for Guntur, 09-11-2026, method=1, school=0.
    t, meta = prayer_times_hours(2026, 11, 9, 16.3067, 80.4365, "KARACHI", "SHAFI")
    print("ours (Karachi/Shafi) vs Aladhan 04:55 06:09 11:52 15:10 17:35 18:49")
    for k in ("FAJR", "SUNRISE", "DHUHR", "ASR", "MAGHRIB", "ISHA"):
        print(f"  {k:8s} {to_local(None, t[k], 5.5)}")
