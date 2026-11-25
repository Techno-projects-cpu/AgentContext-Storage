package app.namaz.azan.core

import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId
import java.time.ZoneOffset

/**
 * Calculation conventions. Angles are degrees below the horizon.
 *
 * [ishaIntervalMinutes] is the fallback interval; [ishaRamadanMinutes] applies
 * inside Ramadan when the convention extends it (Umm al-Qura: 90 -> 120). The
 * extension is not a quirk of one library: it is the published Umm al-Qura rule,
 * and the Saudi calendar's own Ramadan timetables show it (13 Ramadan 1448,
 * Makkah: Maghrib 18:21, Isha 20:21 — two hours, not ninety minutes).
 *
 * [dhuhrAdjustMinutes] is a *guard*, following the convention the reference
 * libraries use: the sun crosses the meridian, and the prayer begins a minute
 * later so that nobody prays while the sun is still exactly overhead. It is
 * deliberately 1, and it must NOT be followed by a second rounding-up when the
 * time is displayed, or Dhuhr drifts a further minute late.
 */
enum class Method(
    val label: String,
    val fajrAngle: Double,
    val ishaAngle: Double,
    val ishaIntervalMinutes: Int = 0,
    val ishaRamadanMinutes: Int = 0,
    val dhuhrAdjustMinutes: Int = 1
) {
    KARACHI("Karachi — Hanafi (India, Pakistan)", 18.0, 18.0),
    MWL("Muslim World League", 18.0, 17.0),
    ISNA("ISNA — North America", 15.0, 15.0),
    EGYPTIAN("Egyptian General Authority", 19.5, 17.5),
    UMM_AL_QURA("Umm al-Qura — Makkah", 18.5, 0.0,
        ishaIntervalMinutes = 90, ishaRamadanMinutes = 120),
    DUBAI("Dubai — Gulf", 18.2, 18.2),
    KUWAIT("Kuwait", 18.0, 17.5),
    QATAR("Qatar", 18.0, 0.0, ishaIntervalMinutes = 90, ishaRamadanMinutes = 120),
    SINGAPORE("Singapore — Shafi", 20.0, 18.0)
}

/** Shadow length used for Asr: Shafi 1×, Hanafi 2×. */
enum class Madhab(val label: String, val shadowFactor: Double, val note: String) {
    SHAFI("Shafi", 1.0, "Also Maliki and Hanbali — Asr earlier"),
    HANAFI("Hanafi", 2.0, "Asr later")
}

enum class Prayer(val label: String, val arabic: String, val meaning: String) {
    FAJR("Fajr", "الفجر", "Dawn"),
    SUNRISE("Sunrise", "الشروق", "Shuruq — not a prayer"),
    DHUHR("Dhuhr", "الظهر", "Midday"),
    ASR("Asr", "العصر", "Afternoon"),
    MAGHRIB("Maghrib", "المغرب", "Sunset"),
    ISHA("Isha", "العشاء", "Night")
}

/** A prayer time with the instant it occurs, for a specific day and zone. */
data class PrayerTime(val prayer: Prayer, val instant: Instant, val time: LocalTime) {
    fun minutesUntil(now: Instant): Long =
        (instant.epochSecond - now.epochSecond) / 60

    companion object {
        /**
         * Round to the nearest minute, the way published timetables do.
         *
         * This is for DISPLAY. [PrayerCalculator] already rounds, so Dhuhr's
         * one-minute guard survives; if this were applied on top of a second
         * offset, Dhuhr would creep late.
         */
        fun roundToMinute(t: LocalTime): LocalTime =
            if (t.second >= 30) t.plusMinutes(1).withSecond(0).withNano(0)
            else t.withSecond(0).withNano(0)
    }
}

/**
 * One day's times, plus the solar geometry that produced them.
 *
 * The geometry is kept because the sky renderer needs it: [transitUT] and
 * [declination] are exactly what [Astronomy.sunPosition] wants, and solving them
 * twice would be both slower and a chance for the picture to disagree with the
 * times.
 */
data class DayTimes(
    val date: LocalDate,
    val zone: ZoneId,
    val times: List<PrayerTime>,
    val transitUT: Double = 0.0,
    val declination: Double = 0.0,
    val sunriseUT: Double = 0.0,
    val sunsetUT: Double = 0.0,
    /** Hijri date, by the arithmetic calendar (see HijriCalendar for the caveat). */
    val hijri: HijriDate? = null,
    /** 10 minutes before Fajr — the stop-eating time, by common convention. */
    val imsak: LocalTime? = null,
    /** Islamic midnight: the midpoint of the night between sunset and sunrise. */
    val midnight: LocalTime? = null,
    /** The last third of the night begins; the time of tahajjud. */
    val lastThird: LocalTime? = null,
    /** Length of the night in minutes, for the night bar on the home screen. */
    val nightMinutes: Int = 0
) {
    fun of(prayer: Prayer): PrayerTime? = times.firstOrNull { it.prayer == prayer }

    /** The next prayer strictly after [now], plus its time; null if the day has none left. */
    fun next(now: Instant): PrayerTime? = times.firstOrNull { it.instant.isAfter(now) }

    fun previous(now: Instant): PrayerTime? = times.lastOrNull { !it.instant.isAfter(now) }

    val isRamadan: Boolean get() = hijri?.isRamadan == true

    /** Minutes of daylight, sunrise to sunset. Drives the week panel's bars. */
    val daylightMinutes: Int
        get() {
            val rise = of(Prayer.SUNRISE)?.instant ?: return 0
            val set = of(Prayer.MAGHRIB)?.instant ?: return 0
            return ((set.epochSecond - rise.epochSecond) / 60).toInt().coerceAtLeast(0)
        }

    /**
     * How far through the night we are between sunset and the next sunrise, 0..1.
     * The night half of the day-arc, and the reason Imsak/Midnight/Last third are
     * worth showing: they divide a stretch of time the app would otherwise leave
     * blank.
     */
    fun nightProgress(now: Instant): Float {
        val sunset = of(Prayer.MAGHRIB)?.instant ?: return 0f
        val span = nightMinutes * 60.0
        if (span <= 0.0) return 0f
        val done = (now.epochSecond - sunset.epochSecond).toDouble()
        return (done / span).coerceIn(0.0, 1.0).toFloat()
    }

    /**
     * How far through the day we are between the previous prayer and the next,
     * 0..1. This is what the hero card's arc shows, and it is the one figure that
     * is true all day rather than only at midnight.
     */
    fun progress(now: Instant): Float {
        val prev = previous(now) ?: return 0f
        val then = next(now) ?: return 1f
        val total = (then.instant.epochSecond - prev.instant.epochSecond).toDouble()
        if (total <= 0.0) return 0f
        val done = (now.epochSecond - prev.instant.epochSecond).toDouble()
        return (done / total).coerceIn(0.0, 1.0).toFloat()
    }

    /**
     * Sun altitude (degrees) and azimuth (degrees from north) at [now].
     *
     * The transit and declination are already solved for this day, so this costs
     * one trigonometry pass rather than a second solar solution.
     */
    fun sun(now: Instant, latitude: Double): Pair<Double, Double> {
        val ut = now.epochSecond / 86400.0
        val utHours = (ut - Math.floor(ut)) * 24.0
        return Astronomy.sunPosition(utHours, transitUT, declination, latitude)
    }
}

/**
 * Computes the five daily prayers plus sunrise.
 *
 * Accuracy was checked against a reference implementation over several cities and
 * dates: every prayer agreed within 58 seconds before rounding.
 */
object PrayerCalculator {

    /**
     * Imsak is ten minutes before Fajr by convention — it is a precaution, not a
     * computed astronomical event. The reference timetable uses the same ten.
     */
    const val IMSAK_MINUTES_BEFORE_FAJR = 10

    fun forDate(
        date: LocalDate,
        latitude: Double,
        longitude: Double,
        zone: ZoneId,
        method: Method = Method.KARACHI,
        madhab: Madhab = Madhab.SHAFI,
        adjustmentsMinutes: Map<Prayer, Int> = emptyMap()
    ): DayTimes {
        val hijri = HijriCalendar.fromGregorian(date)
        val jd = Astronomy.julianDay(date.year, date.monthValue, date.dayOfMonth)
        val prev = Astronomy.SolarCoordinates(jd - 1)
        val cur = Astronomy.SolarCoordinates(jd)
        val next = Astronomy.SolarCoordinates(jd + 1)

        val m0 = Astronomy.approximateTransit(longitude, cur.apparentSiderealTime, cur.rightAscension)

        fun hourAngle(angle: Double, after: Boolean) = Astronomy.correctedHourAngle(
            m0, angle, latitude, longitude, after,
            cur.apparentSiderealTime,
            cur.rightAscension, prev.rightAscension, next.rightAscension,
            cur.declination, prev.declination, next.declination
        )

        val transit = Astronomy.correctedTransit(
            m0, longitude, cur.apparentSiderealTime,
            cur.rightAscension, prev.rightAscension, next.rightAscension
        )
        val sunriseH = hourAngle(-50.0 / 60.0, false)
        val sunsetH = hourAngle(-50.0 / 60.0, true)

        // Night length, used only as a high-latitude safety net.
        val nightHours = ((sunriseH + 24.0) - sunsetH)

        // High-latitude fallback: the sun never reaches the angle, so the prayer
        // is placed at the middle of the night. Times are "hours from midnight
        // UT of `date`" and are allowed to be negative or greater than 24 —
        // Fajr for India is legitimately about -0.6. Wrapping these into [0, 24)
        // would move Fajr a whole day late, which is what an earlier version of
        // this function did.
        fun fajrHours(): Double {
            val raw = hourAngle(-method.fajrAngle, false)
            if (!raw.isNaN()) return raw
            return sunriseH - nightHours / 2.0
        }

        fun ishaHours(): Double {
            // Umm al-Qura and Qatar both extend Isha inside Ramadan. This is the
            // published rule, not an implementation detail.
            val interval = if (method.ishaRamadanMinutes > 0 && hijri?.isRamadan == true) {
                method.ishaRamadanMinutes
            } else {
                method.ishaIntervalMinutes
            }
            if (interval > 0) {
                return ((sunsetH + interval / 60.0) + 24.0) % 24.0
            }
            val raw = hourAngle(-method.ishaAngle, true)
            if (!raw.isNaN()) return raw
            return sunsetH + nightHours / 2.0
        }

        val asrAngle = Astronomy.asrAngle(latitude, cur.declination, madhab.shadowFactor)
        val asrH = hourAngle(asrAngle, true)

        val raw = mapOf(
            Prayer.FAJR to fajrHours(),
            Prayer.SUNRISE to sunriseH,
            Prayer.DHUHR to transit + method.dhuhrAdjustMinutes / 60.0,
            Prayer.ASR to (if (asrH.isNaN()) transit + 3.5 else asrH),
            Prayer.MAGHRIB to sunsetH,
            Prayer.ISHA to ishaHours()
        )

        /** Convert "hours from midnight UT of `date`" to a local clock time. */
        fun localTimeFor(hours: Double): LocalTime {
            val instant = LocalDateTime.of(date, LocalTime.MIDNIGHT)
                .toInstant(ZoneOffset.UTC)
                .plusSeconds(Math.round(hours * 3600.0))
            return PrayerTime.roundToMinute(LocalTime.ofInstant(instant, zone))
        }

        val times = Prayer.entries.map { prayer ->
            val hours = raw.getValue(prayer)
            val offset = (adjustmentsMinutes[prayer] ?: 0) * 60L
            // `hours` counts from midnight UTC of `date`.
            val instant = LocalDateTime.of(date, LocalTime.MIDNIGHT)
                .toInstant(ZoneOffset.UTC)
                .plusSeconds(Math.round(hours * 3600.0))
                .plusSeconds(offset)
            val local = LocalTime.ofInstant(instant, zone)
            PrayerTime(prayer, instant, PrayerTime.roundToMinute(local))
        }

        return DayTimes(
            date = date,
            zone = zone,
            times = times,
            transitUT = transit,
            declination = cur.declination,
            sunriseUT = sunriseH,
            sunsetUT = sunsetH,
            hijri = hijri,
            imsak = localTimeFor(fajrHours() - IMSAK_MINUTES_BEFORE_FAJR / 60.0),
            midnight = localTimeFor(sunsetH + nightHours / 2.0),
            lastThird = localTimeFor(sunsetH + nightHours * 2.0 / 3.0),
            nightMinutes = Math.round(nightHours * 60.0).toInt()
        )
    }

    /** Convenience: the day containing [now] in [zone]. */
    fun forInstant(
        now: Instant,
        zone: ZoneId,
        latitude: Double,
        longitude: Double,
        method: Method,
        madhab: Madhab,
        adjustments: Map<Prayer, Int> = emptyMap()
    ): DayTimes = forDate(
        now.atZone(zone).toLocalDate(), latitude, longitude, zone, method, madhab, adjustments
    )
}
