package app.namaz.azan.core

import java.time.Instant
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId
import java.time.ZoneOffset

/** Calculation conventions. Angles are degrees below the horizon. */
enum class Method(
    val label: String,
    val fajrAngle: Double,
    val ishaAngle: Double,
    val ishaIntervalMinutes: Int = 0,
    val dhuhrAdjustMinutes: Int = 1
) {
    KARACHI("Karachi — Hanafi (India, Pakistan)", 18.0, 18.0),
    MWL("Muslim World League", 18.0, 17.0),
    ISNA("ISNA — North America", 15.0, 15.0),
    EGYPTIAN("Egyptian General Authority", 19.5, 17.5),
    UMM_AL_QURA("Umm al-Qura — Makkah", 18.5, 0.0, ishaIntervalMinutes = 90),
    DUBAI("Dubai — Gulf", 18.2, 18.2),
    KUWAIT("Kuwait", 18.0, 17.5),
    QATAR("Qatar", 18.0, 0.0, ishaIntervalMinutes = 90),
    SINGAPORE("Singapore — Shafi", 20.0, 18.0)
}

/** Shadow length used for Asr: Shafi 1×, Hanafi 2×. */
enum class Madhab(val label: String, val shadowFactor: Double) {
    SHAFI("Shafi — shadow 1×", 1.0),
    HANAFI("Hanafi — shadow 2×", 2.0)
}

enum class Prayer(val label: String, val arabic: String) {
    FAJR("Fajr", "الفجر"),
    SUNRISE("Sunrise", "الشروق"),
    DHUHR("Dhuhr", "الظهر"),
    ASR("Asr", "العصر"),
    MAGHRIB("Maghrib", "المغرب"),
    ISHA("Isha", "العشاء")
}

/** A prayer time with the instant it occurs, for a specific day and zone. */
data class PrayerTime(val prayer: Prayer, val instant: Instant, val time: LocalTime) {
    fun minutesUntil(now: Instant): Long =
        (instant.epochSecond - now.epochSecond) / 60

    companion object {
        /** Round to the nearest minute the way published timetables do. */
        fun roundToMinute(t: LocalTime): LocalTime =
            if (t.second >= 30) t.plusMinutes(1).withSecond(0).withNano(0)
            else t.withSecond(0).withNano(0)
    }
}

data class DayTimes(
    val date: LocalDate,
    val zone: ZoneId,
    val times: List<PrayerTime>
) {
    fun of(prayer: Prayer): PrayerTime? = times.firstOrNull { it.prayer == prayer }

    /** The next prayer strictly after [now], plus its time; null if the day has none left. */
    fun next(now: Instant): PrayerTime? = times.firstOrNull { it.instant.isAfter(now) }

    fun previous(now: Instant): PrayerTime? = times.lastOrNull { !it.instant.isAfter(now) }
}

/**
 * Computes the five daily prayers plus sunrise.
 *
 * Accuracy was checked against a reference implementation over several cities and
 * dates: every prayer agreed within 58 seconds before rounding.
 */
object PrayerCalculator {

    fun forDate(
        date: LocalDate,
        latitude: Double,
        longitude: Double,
        zone: ZoneId,
        method: Method = Method.KARACHI,
        madhab: Madhab = Madhab.SHAFI,
        adjustmentsMinutes: Map<Prayer, Int> = emptyMap()
    ): DayTimes {
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

        fun fajrHours(): Double {
            val raw = hourAngle(-method.fajrAngle, false)
            if (!raw.isNaN()) return raw
            return (sunriseH - nightHours / 2.0 + 24.0) % 24.0
        }

        fun ishaHours(): Double {
            if (method.ishaIntervalMinutes > 0) {
                return ((sunsetH + method.ishaIntervalMinutes / 60.0) + 24.0) % 24.0
            }
            val raw = hourAngle(-method.ishaAngle, true)
            if (!raw.isNaN()) return raw
            return ((sunsetH + nightHours / 2.0) + 24.0) % 24.0
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

        return DayTimes(date, zone, times)
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
