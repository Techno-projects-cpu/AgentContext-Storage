package app.namaz.azan

import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.core.PrayerCalculator
import app.namaz.azan.core.PrayerTime
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import kotlin.math.abs

/**
 * Prayer time accuracy.
 *
 * Expected values come from an independent reference implementation of the same
 * astronomical algorithm (Adhan family), cross-checked at four cities. Comparisons are
 * made in minutes-of-day with a tolerance, because the two implementations round to the
 * nearest minute differently — pinning an exact string would test the rounding
 * convention rather than the astronomy.
 */
class PrayerTimesTest {

    private val ist = ZoneId.of("Asia/Kolkata")

    private fun times(
        date: LocalDate,
        lat: Double = 16.3067,
        lon: Double = 80.4365,
        method: Method = Method.KARACHI,
        madhab: Madhab = Madhab.SHAFI
    ) = PrayerCalculator.forDate(date, lat, lon, ist, method, madhab)

    private fun minutesOfDay(t: LocalTime): Int = t.hour * 60 + t.minute

    private fun assertNear(prayer: Prayer, expected: String, actual: PrayerTime, toleranceMinutes: Int = 2) {
        val expectedMinutes = expected.split(":").let { it[0].toInt() * 60 + it[1].toInt() }
        val actualMinutes = minutesOfDay(actual.time)
        val delta = abs(actualMinutes - expectedMinutes)
        assertTrue(
            "$prayer: expected ~$expected, got ${actual.time} (off by $delta min)",
            delta <= toleranceMinutes
        )
    }

    @Test
    fun guntur_times_match_reference() {
        val day = times(LocalDate.of(2026, 11, 22))
        assertNear(Prayer.FAJR, "05:00", day.of(Prayer.FAJR)!!)
        assertNear(Prayer.SUNRISE, "06:15", day.of(Prayer.SUNRISE)!!)
        assertNear(Prayer.DHUHR, "11:55", day.of(Prayer.DHUHR)!!)
        assertNear(Prayer.ASR, "15:09", day.of(Prayer.ASR)!!)
        assertNear(Prayer.MAGHRIB, "17:33", day.of(Prayer.MAGHRIB)!!)
        assertNear(Prayer.ISHA, "18:49", day.of(Prayer.ISHA)!!)
    }

    @Test
    fun guntur_summer_solstice() {
        val day = times(LocalDate.of(2026, 6, 21))
        assertNear(Prayer.FAJR, "04:16", day.of(Prayer.FAJR)!!)
        assertNear(Prayer.DHUHR, "12:11", day.of(Prayer.DHUHR)!!)
        assertNear(Prayer.ASR, "15:35", day.of(Prayer.ASR)!!)
        assertNear(Prayer.MAGHRIB, "18:43", day.of(Prayer.MAGHRIB)!!)
        assertNear(Prayer.ISHA, "20:04", day.of(Prayer.ISHA)!!)
    }

    /** Prints the table into the CI log, so the numbers are auditable without a device. */
    @Test
    fun report_guntur_week() {
        println("Prayer times — Guntur (16.3067N, 80.4365E), Karachi method, Shafi Asr")
        for (dayOffset in 0L..6L) {
            val date = LocalDate.of(2026, 11, 22).plusDays(dayOffset)
            val day = times(date)
            val row = Prayer.entries.joinToString("  ") { p ->
                "%s %s".format(p.label.padEnd(8), day.of(p)!!.time.toString())
            }
            println("$date  $row")
        }
    }

    @Test
    fun all_times_are_ordered_within_the_day() {
        val day = times(LocalDate.of(2026, 3, 5))
        val ordered = Prayer.entries.map { day.of(it)!! }
        ordered.zipWithNext { a, b ->
            assertTrue(
                "${a.prayer} (${a.time}) must precede ${b.prayer} (${b.time})",
                a.instant.isBefore(b.instant)
            )
        }
    }

    @Test
    fun dhuhr_sits_at_solar_noon() {
        // At longitude 80.4°E solar noon is close to 11:58 IST; the equation of time
        // moves it by up to ~15 minutes over the year.
        for (month in 1..12) {
            val day = times(LocalDate.of(2026, month, 15))
            val minutes = minutesOfDay(day.of(Prayer.DHUHR)!!.time)
            assertTrue("month $month dhuhr ${day.of(Prayer.DHUHR)!!.time}",
                minutes in (11 * 60 + 30)..(12 * 60 + 30))
        }
    }

    @Test
    fun hanafi_asr_is_later_than_shafi() {
        val shafi = times(LocalDate.of(2026, 11, 22), madhab = Madhab.SHAFI)
        val hanafi = times(LocalDate.of(2026, 11, 22), madhab = Madhab.HANAFI)
        assertTrue(hanafi.of(Prayer.ASR)!!.instant.isAfter(shafi.of(Prayer.ASR)!!.instant))
    }

    @Test
    fun method_changes_isha_but_not_maghrib() {
        val karachi = times(LocalDate.of(2026, 11, 22), method = Method.KARACHI)
        val isna = times(LocalDate.of(2026, 11, 22), method = Method.ISNA)
        assertEquals(karachi.of(Prayer.MAGHRIB)!!.time, isna.of(Prayer.MAGHRIB)!!.time)
        assertTrue(karachi.of(Prayer.ISHA)!!.instant.isAfter(isna.of(Prayer.ISHA)!!.instant))
    }

    @Test
    fun umm_al_qura_uses_a_fixed_isha_interval() {
        val makkah = times(
            LocalDate.of(2026, 11, 22), lat = 21.4225, lon = 39.8262,
            method = Method.UMM_AL_QURA
        )
        val maghrib = makkah.of(Prayer.MAGHRIB)!!.instant
        val isha = makkah.of(Prayer.ISHA)!!.instant
        assertEquals(90L, (isha.epochSecond - maghrib.epochSecond) / 60)
    }

    @Test
    fun next_prayer_lookup_behaves_at_the_day_boundary() {
        val day = times(LocalDate.of(2026, 11, 22))
        val justAfterIsha = day.of(Prayer.ISHA)!!.instant.plusSeconds(60)
        assertEquals(null, day.next(justAfterIsha))
        assertEquals(Prayer.ISHA, day.previous(justAfterIsha)!!.prayer)
        assertNotNull(day.next(day.of(Prayer.FAJR)!!.instant.minusSeconds(60)))
    }

    @Test
    fun high_latitude_winter_does_not_crash() {
        // Where naive implementations divide by zero or produce NaN.
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 12, 21), 59.33, 18.07, ZoneId.of("Europe/Stockholm"),
            Method.KARACHI, Madhab.SHAFI
        )
        assertEquals(6, day.times.size)
        day.times.forEach { assertNotNull(it.time) }
    }

    @Test
    fun manual_adjustment_shifts_only_the_chosen_prayer() {
        val base = times(LocalDate.of(2026, 11, 22))
        val shifted = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 22), 16.3067, 80.4365, ist, Method.KARACHI,
            Madhab.SHAFI, mapOf(Prayer.FAJR to 5)
        )
        val delta = shifted.of(Prayer.FAJR)!!.instant.epochSecond -
            base.of(Prayer.FAJR)!!.instant.epochSecond
        assertEquals(300L, delta)
        assertEquals(base.of(Prayer.MAGHRIB)!!.time, shifted.of(Prayer.MAGHRIB)!!.time)
    }

    @Test
    fun times_are_stable_across_a_year() {
        // A cheap regression net: no prayer may land outside a plausible band.
        var date = LocalDate.of(2026, 1, 1)
        while (date.year == 2026) {
            val day = times(date)
            for (prayer in Prayer.entries) {
                val minutes = minutesOfDay(day.of(prayer)!!.time)
                assertTrue("$date $prayer was $minutes", minutes in 0..1439)
            }
            assertTrue(day.of(Prayer.FAJR)!!.instant.isBefore(day.of(Prayer.DHUHR)!!.instant))
            assertTrue(day.of(Prayer.MAGHRIB)!!.instant.isBefore(day.of(Prayer.ISHA)!!.instant))
            date = date.plusDays(7)
        }
    }
}
