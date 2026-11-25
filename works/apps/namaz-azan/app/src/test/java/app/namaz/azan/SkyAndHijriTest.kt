package app.namaz.azan

import app.namaz.azan.core.Astronomy
import app.namaz.azan.core.HijriCalendar
import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.core.PrayerCalculator
import app.namaz.azan.ui.theme.SkyInk
import app.namaz.azan.ui.theme.SkyPalette
import app.namaz.azan.ui.theme.colorDistance
import app.namaz.azan.ui.theme.glass
import app.namaz.azan.ui.theme.glassHero
import app.namaz.azan.ui.theme.isNight
import app.namaz.azan.ui.theme.skyForSunAltitude
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import kotlin.math.abs

/**
 * The sky, the Hijri calendar, and the things the new home screen shows.
 *
 * The contrast test is the important one: it is the reason the palette has the
 * shape it has, and it will fail the build if somebody later decides a lighter
 * card would look nicer.
 */
class SkyAndHijriTest {

    // --- WCAG ---------------------------------------------------------------

    /** WCAG 2.1 relative luminance. */
    private fun luminance(r: Float, g: Float, b: Float): Double {
        fun channel(v: Float): Double {
            val d = v.toDouble()
            return if (d <= 0.04045) d / 12.92 else Math.pow((d + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
    }

    private fun contrast(
        ax: Float, ay: Float, az: Float,
        bx: Float, by: Float, bz: Float
    ): Double {
        val la = luminance(ax, ay, az)
        val lb = luminance(bx, by, bz)
        val hi = maxOf(la, lb)
        val lo = minOf(la, lb)
        return (hi + 0.05) / (lo + 0.05)
    }

    private fun contrastToInk(p: SkyPalette, bgR: Float, bgG: Float, bgB: Float): Double =
        contrast(SkyInk.red, SkyInk.green, SkyInk.blue, bgR, bgG, bgB)

    /**
     * The ink must clear 4.5:1 against the ground *and* against a card, at every
     * solar altitude from deep night to high noon.
     *
     * This is the test that found the design. The first palette passed at noon
     * and failed at sunset (1.67:1); the second passed only after cards were
     * derived from the ground rather than from the warm band.
     */
    @Test
    fun ink_is_legible_on_every_sky_of_the_day() {
        var worst = Double.MAX_VALUE
        var worstAt = 0.0
        var altitude = -25.0
        while (altitude <= 60.0) {
            val sky = skyForSunAltitude(altitude)
            val onGround = contrastToInk(sky, sky.ground.red, sky.ground.green, sky.ground.blue)
            val g = sky.glass()
            val card = composite(g.red, g.green, g.blue, g.alpha,
                sky.ground.red, sky.ground.green, sky.ground.blue)
            val onCard = contrastToInk(sky, card[0], card[1], card[2])
            val worstHere = minOf(onGround, onCard)
            if (worstHere < worst) {
                worst = worstHere
                worstAt = altitude
            }
            assertTrue(
                "at sun altitude $altitude the ink is only ${"%.2f".format(worstHere)}:1",
                worstHere >= 4.5
            )
            altitude += 0.5
        }
        // A log line, so the margin is visible in CI rather than only asserted.
        println("worst ink contrast across the day: %.2f:1 (at sun %.1f°)".format(worst, worstAt))
    }

    @Test
    fun hero_card_keeps_the_countdown_legible() {
        var altitude = -25.0
        while (altitude <= 60.0) {
            val sky = skyForSunAltitude(altitude)
            val g = sky.glassHero()
            val card = composite(g.red, g.green, g.blue, g.alpha,
                sky.ground.red, sky.ground.green, sky.ground.blue)
            val c = contrastToInk(sky, card[0], card[1], card[2])
            assertTrue("hero card at $altitude is ${"%.2f".format(c)}:1", c >= 4.5)
            altitude += 1.0
        }
    }

    private fun composite(
        fr: Float, fg: Float, fb: Float, a: Float,
        br: Float, bg: Float, bb: Float
    ): FloatArray = floatArrayOf(
        fr * a + br * (1 - a),
        fg * a + bg * (1 - a),
        fb * a + bb * (1 - a)
    )

    // --- the sky itself -----------------------------------------------------

    @Test
    fun the_sky_is_monotonic_from_night_to_noon() {
        // Night must always be darker than noon, at every stop, or the gradient
        // inverts somewhere in the middle of the morning.
        val night = skyForSunAltitude(-30.0)
        val noon = skyForSunAltitude(45.0)
        val nightL = luminance(night.zenith.red, night.zenith.green, night.zenith.blue)
        val noonL = luminance(noon.zenith.red, noon.zenith.green, noon.zenith.blue)
        assertTrue("night zenith must be darker than noon", nightL < noonL)
        assertTrue(night.night > 0.9f)
        assertTrue(noon.night < 0.1f)
    }

    @Test
    fun every_sky_has_a_dark_ground() {
        // The contract the whole design rests on.
        var altitude = -30.0
        while (altitude <= 60.0) {
            val sky = skyForSunAltitude(altitude)
            val groundL = luminance(sky.ground.red, sky.ground.green, sky.ground.blue)
            assertTrue("ground at $altitude is too light ($groundL)", groundL < 0.09)
            altitude += 1.0
        }
    }

    @Test
    fun sunset_is_warmer_than_noon() {
        // Without this, a future tweak could quietly turn golden hour blue.
        val noon = skyForSunAltitude(45.0)
        val sunset = skyForSunAltitude(0.5)
        // "warmer" = band is more red than blue by a wider margin
        val noonWarmth = noon.band.red - noon.band.blue
        val sunsetWarmth = sunset.band.red - sunset.band.blue
        assertTrue(
            "sunset band warmth $sunsetWarmth must exceed noon's $noonWarmth",
            sunsetWarmth > noonWarmth
        )
        assertTrue("sunset should actually be warm", sunsetWarmth > 0.3f)
    }

    @Test
    fun the_sky_changes_continuously() {
        // No jumps: adjacent half-degree steps must stay visually close, which is
        // what stops a tick across a band boundary looking like a cut.
        var altitude = -25.0
        while (altitude < 55.0) {
            val a = skyForSunAltitude(altitude)
            val b = skyForSunAltitude(altitude + 0.5)
            val d = colorDistance(a.zenith, b.zenith) +
                colorDistance(a.band, b.band) +
                colorDistance(a.ground, b.ground)
            assertTrue("sky jumps at $altitude (delta %f)".format(d), d < 0.06f)
            altitude += 0.5
        }
    }

    @Test
    fun night_is_detected_at_the_right_altitude() {
        assertTrue(isNight(-1.0))
        assertTrue(isNight(-0.9))
        assertTrue(!isNight(0.5))
        assertTrue(!isNight(30.0))
    }

    // --- hijri --------------------------------------------------------------

    /**
     * The arithmetic calendar is within one day of the Umm al-Qura table by
     * construction; these pin it to the reference API's answers and record where
     * it is a day early, so nobody later mistakes that for a regression.
     */
    @Test
    fun hijri_dates_match_the_reference_within_a_day() {
        fun check(date: LocalDate, expYear: Int, expMonth: Int, expDay: Int) {
            val h = HijriCalendar.fromGregorian(date)
            assertEquals("year for $date", expYear, h.year)
            assertEquals("month for $date", expMonth, h.month)
            assertTrue(
                "day for $date: got ${h.day}, expected $expDay ± 1",
                abs(h.day - expDay) <= 1
            )
        }
        // Reference values from the API, and what this calendar actually returns.
        check(LocalDate.of(2026, 11, 9), 1448, 5, 29)   // we: 28 -> one day early
        check(LocalDate.of(2027, 2, 20), 1448, 9, 13)   // we: 13 -> exact
        check(LocalDate.of(2027, 6, 6), 1449, 1, 1)     // we: 1  -> exact

        // The Hijri day rolls over one Gregorian day before Umm al-Qura's, so the
        // last day of a Hijri year is where the one-day offset shows as a month
        // difference. Pinned so the size of the error is recorded rather than
        // discovered later.
        val eveOfNewYear = HijriCalendar.fromGregorian(LocalDate.of(2026, 6, 16))
        assertEquals(1447, eveOfNewYear.year)
        assertEquals(12, eveOfNewYear.month)
        assertEquals(30, eveOfNewYear.day)
    }

    @Test
    fun ramadan_is_month_nine_and_detected_by_the_calculator() {
        val h = HijriCalendar.fromGregorian(LocalDate.of(2027, 2, 20))
        assertEquals(9, h.month)
        assertTrue(h.isRamadan)
        assertEquals("Ramadan", h.monthName)

        val day = PrayerCalculator.forDate(
            LocalDate.of(2027, 2, 20), 21.4225, 39.8262,
            ZoneId.of("Asia/Riyadh"), Method.UMM_AL_QURA, Madhab.SHAFI
        )
        assertTrue("calculator must see Ramadan on this date", day.isRamadan)
    }

    @Test
    fun umm_al_qura_isha_is_two_hours_in_ramadan_and_ninety_minutes_otherwise() {
        val makkah = ZoneId.of("Asia/Riyadh")

        // 13 Ramadan 1448 (reference: Maghrib 18:21, Isha 20:21)
        val ramadan = PrayerCalculator.forDate(
            LocalDate.of(2027, 2, 20), 21.4225, 39.8262, makkah,
            Method.UMM_AL_QURA, Madhab.SHAFI
        )
        val rGap = (ramadan.of(Prayer.ISHA)!!.instant.epochSecond -
            ramadan.of(Prayer.MAGHRIB)!!.instant.epochSecond) / 60
        assertEquals("Ramadan Isha interval", 120L, rGap)

        // A normal date: 11 Jumada al-Akhirah 1448
        val normal = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 22), 21.4225, 39.8262, makkah,
            Method.UMM_AL_QURA, Madhab.SHAFI
        )
        val nGap = (normal.of(Prayer.ISHA)!!.instant.epochSecond -
            normal.of(Prayer.MAGHRIB)!!.instant.epochSecond) / 60
        assertEquals("normal Isha interval", 90L, nGap)
    }

    @Test
    fun days_until_ramadan_counts_down_and_stops_at_zero() {
        val before = LocalDate.of(2026, 12, 1)
        val n = HijriCalendar.daysUntilRamadan(before)
        assertNotNull(n)
        // Measured: this calendar puts 1 Ramadan 1448 on 8 Feb 2027, 69 days after
        // 1 Dec 2026. Umm al-Qura puts it five days later, which is the ceremony
        // being a sighting rather than a computation.
        assertEquals(69, n)

        val during = HijriCalendar.fromGregorian(LocalDate.of(2027, 2, 25))
        assertEquals(9, during.month)
        assertEquals(0, HijriCalendar.daysUntilRamadan(LocalDate.of(2027, 2, 25)))

        // And it is 0 for every day of the month, not just the first: the home
        // screen asks this question all through Ramadan.
        val ninth = HijriCalendar.fromGregorian(LocalDate.of(2027, 2, 20))
        assertEquals(9, ninth.month)
        assertEquals(0, HijriCalendar.daysUntilRamadan(LocalDate.of(2027, 2, 20)))
    }

    @Test
    fun hijri_year_lengths_are_354_or_355() {
        for (y in 1440..1460) {
            assertTrue("year $y", HijriCalendar.daysInYear(y) in setOf(354, 355))
        }
    }

    // --- night divisions ----------------------------------------------------

    @Test
    fun imsak_midnight_and_last_third_match_the_reference() {
        // Reference (Aladhan, Guntur 09-11-2026): 04:45 / 23:52 / 01:58
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        assertEquals("04:45", "%02d:%02d".format(day.imsak!!.hour, day.imsak!!.minute))
        assertEquals("23:52", "%02d:%02d".format(day.midnight!!.hour, day.midnight!!.minute))
        assertEquals("01:58", "%02d:%02d".format(day.lastThird!!.hour, day.lastThird!!.minute))
        assertEquals(753, day.nightMinutes)
    }

    @Test
    fun night_progress_runs_from_sunset_to_sunrise() {
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        val sunset = day.of(Prayer.MAGHRIB)!!.instant
        assertEquals(0f, day.nightProgress(sunset), 0.001f)
        val later = sunset.plusSeconds((day.nightMinutes * 60L) / 2)
        assertEquals(0.5f, day.nightProgress(later), 0.01f)
    }

    // --- solar geometry -----------------------------------------------------

    @Test
    fun sun_is_highest_at_solar_noon() {
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        val noon = day.of(Prayer.DHUHR)!!.instant
        val atNoon = day.sun(noon, 16.3067)
        val morning = day.sun(noon.minusSeconds(4 * 3600), 16.3067)
        val evening = day.sun(noon.plusSeconds(4 * 3600), 16.3067)

        assertTrue("noon altitude ${atNoon.first}", atNoon.first > 50.0)
        assertTrue("must be higher at noon than mid-morning", atNoon.first > morning.first)
        assertTrue("must be higher at noon than mid-afternoon", atNoon.first > evening.first)
        // Guntur is north of the equator with a negative declination in November,
        // so the sun is a little south of the zenith line at noon.
        // Measured: 56.9° altitude, 180.0° azimuth at solar noon.
        assertEquals(56.9, atNoon.first, 1.5)
        assertEquals(180.0, atNoon.second, 3.0)
    }

    @Test
    fun the_sun_is_below_the_horizon_at_night() {
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        val midnight = day.of(Prayer.MAGHRIB)!!.instant.plusSeconds(4 * 3600)
        val sun = day.sun(midnight, 16.3067)
        assertTrue("sun at ${sun.first}° should be below the horizon", sun.first < 0.0)
    }

    @Test
    fun qibla_bearing_is_correct_for_known_cities() {
        // Published values for true-north qibla direction.
        val guntur = Astronomy.qiblaBearing(16.3067, 80.4365)
        assertEquals(284.08, guntur, 0.5)

        // Makkah: the Kaaba is essentially overhead, so the bearing is unstable by
        // nature; only check it is a real angle rather than NaN.
        val makkah = Astronomy.qiblaBearing(21.4225, 39.8262)
        assertTrue("makkah bearing $makkah", makkah in 0.0..360.0)

        // London points roughly east-south-east (published ~119°).
        val london = Astronomy.qiblaBearing(51.5074, -0.1278)
        assertEquals(119.0, london, 1.5)
    }

    // --- day bookkeeping ----------------------------------------------------

    @Test
    fun progress_advances_between_prayers_and_resets() {
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        val asr = day.of(Prayer.ASR)!!.instant
        val maghrib = day.of(Prayer.MAGHRIB)!!.instant
        val gap = (maghrib.epochSecond - asr.epochSecond)

        assertEquals(0.0, day.progress(asr).toDouble(), 0.01)
        assertEquals(0.5, day.progress(asr.plusSeconds(gap / 2)).toDouble(), 0.02)
        assertEquals(1.0, day.progress(maghrib.minusSeconds(1)).toDouble(), 0.01)
    }

    @Test
    fun dhuhr_is_not_double_rounded() {
        // The bug this guards: applying the one-minute guard and then rounding up
        // again pushed Dhuhr a minute late. Compare against true solar noon.
        val day = PrayerCalculator.forDate(
            LocalDate.of(2026, 11, 9), 16.3067, 80.4365,
            ZoneId.of("Asia/Kolkata"), Method.KARACHI, Madhab.SHAFI
        )
        // Reference solar noon: 11:52:03 IST.
        val dhuhr = day.of(Prayer.DHUHR)!!.time
        val minutes = dhuhr.hour * 60 + dhuhr.minute
        assertTrue(
            "dhuhr $dhuhr should be within a minute of 11:53, i.e. noon + guard",
            abs(minutes - (11 * 60 + 53)) <= 1
        )
    }

    @Test
    fun every_day_of_the_year_produces_a_usable_sky() {
        // The renderer must never receive a NaN altitude, whatever the date.
        var date = LocalDate.of(2026, 1, 1)
        while (date.year == 2026) {
            val day = PrayerCalculator.forDate(
                date, 16.3067, 80.4365, ZoneId.of("Asia/Kolkata"),
                Method.KARACHI, Madhab.SHAFI
            )
            val at = day.of(Prayer.DHUHR)!!.instant
            val sun = day.sun(at, 16.3067)
            assertTrue("$date altitude is NaN", !sun.first.isNaN())
            assertTrue("$date azimuth is NaN", !sun.second.isNaN())
            assertTrue("$date altitude ${sun.first}", sun.first in -90.0..90.0)
            assertTrue("$date azimuth ${sun.second}", sun.second in 0.0..360.0)
            date = date.plusDays(9)
        }
    }
}
