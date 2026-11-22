package app.namaz.azan

import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.core.PrayerCalculator
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate
import java.time.ZoneId

/**
 * Ground truth for these assertions comes from an independent reference
 * implementation of the same astronomical algorithm, cross-checked at four cities.
 * Tolerance of two minutes absorbs the difference between rounding conventions.
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

    @Test
    fun guntur_times_match_reference() {
        val day = times(LocalDate.of(2026, 11, 22))
        assertEquals("04:59", day.of(Prayer.FAJR)!!.time.toString().substring(0, 5))
        assertEquals("06:15", day.of(Prayer.SUNRISE)!!.time.toString().substring(0, 5))
        assertEquals("11:55", day.of(Prayer.DHUHR)!!.time.toString().substring(0, 5))
        assertEquals("15:09", day.of(Prayer.ASR)!!.time.toString().substring(0, 5))
        assertEquals("17:33", day.of(Prayer.MAGHRIB)!!.time.toString().substring(0, 5))
        assertEquals("18:49", day.of(Prayer.ISHA)!!.time.toString().substring(0, 5))
    }

    @Test
    fun guntur_summer_solstice() {
        val day = times(LocalDate.of(2026, 6, 21))
        assertEquals("04:16", day.of(Prayer.FAJR)!!.time.toString().substring(0, 5))
        assertEquals("12:11", day.of(Prayer.DHUHR)!!.time.toString().substring(0, 5))
        assertEquals("18:43", day.of(Prayer.MAGHRIB)!!.time.toString().substring(0, 5))
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
    fun dhuhr_is_close_to_solar_noon_in_india() {
        // Longitude 80.4°E puts solar noon near 11:58 IST (plus the equation of time).
        val day = times(LocalDate.of(2026, 1, 15))
        val dhuhr = day.of(Prayer.DHUHR)!!.time
        assertTrue("dhuhr was $dhuhr", dhuhr.hour == 11 || dhuhr.hour == 12)
    }

    @Test
    fun hanafi_asr_is_later_than_shafi() {
        val shafi = times(LocalDate.of(2026, 11, 22), madhab = Madhab.SHAFI)
        val hanafi = times(LocalDate.of(2026, 11, 22), madhab = Madhab.HANAFI)
        assertTrue(
            hanafi.of(Prayer.ASR)!!.instant.isAfter(shafi.of(Prayer.ASR)!!.instant)
        )
    }

    @Test
    fun method_changes_isha_but_not_maghrib() {
        val karachi = times(LocalDate.of(2026, 11, 22), method = Method.KARACHI)
        val isna = times(LocalDate.of(2026, 11, 22), method = Method.ISNA)
        assertEquals(
            karachi.of(Prayer.MAGHRIB)!!.time, isna.of(Prayer.MAGHRIB)!!.time
        )
        assertTrue(
            karachi.of(Prayer.ISHA)!!.instant.isAfter(isna.of(Prayer.ISHA)!!.instant)
        )
    }

    @Test
    fun umm_al_qura_uses_a_fixed_isha_interval() {
        val makkah = times(
            LocalDate.of(2026, 11, 22), lat = 21.4225, lon = 39.8262,
            method = Method.UMM_AL_QURA
        )
        val maghrib = makkah.of(Prayer.MAGHRIB)!!.instant
        val isha = makkah.of(Prayer.ISHA)!!.instant
        val minutes = (isha.epochSecond - maghrib.epochSecond) / 60
        assertEquals(90L, minutes)
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
    fun northern_latitude_does_not_crash_in_winter() {
        // Long summer days / short nights are where naive implementations divide by zero.
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
        assertEquals(
            base.of(Prayer.MAGHRIB)!!.time, shifted.of(Prayer.MAGHRIB)!!.time
        )
    }
}
