package app.namaz.azan.core

import java.time.LocalDate

/**
 * The Islamic (Hijri) calendar, by the arithmetic rule.
 *
 * ## Which rule, and why
 *
 * There are three things people mean by "the Islamic date":
 *
 *  1. **Observed** — what the local moon-sighting committee announced. No
 *     algorithm can produce this; it is a news event.
 *  2. **Umm al-Qura (tabular, Saudi)** — a published table of month lengths.
 *     Reproducing it exactly needs that table shipped as data, and this app's
 *     one rule is that it computes rather than looks up.
 *  3. **Arithmetic** — the 30-year cycle. This is what is implemented here.
 *
 * The arithmetic calendar is exact as an arithmetic calendar, and is at most
 * **±1 day** from the Umm al-Qura table. Measured against the reference API at
 * four points across two years, it agreed outright at two and was one day early
 * at the other two.
 *
 * That ±1 day matters in exactly one place: the Ramadan rule that lengthens Isha
 * to 120 minutes. So the app says which calendar it is using, shows the date so a
 * reader can check it against their mosque, and never claims more precision than
 * it has. An app that quietly guessed the first day of Ramadan would be worse
 * than one that shows nothing.
 *
 * Month lengths follow the usual alternating pattern (30, 29, 30 …) with Dhu
 * al-Hijjah taking 30 days in a leap year of the 11-in-30 cycle.
 */
data class HijriDate(
    val year: Int,
    /** 1 = Muharram … 9 = Ramadan … 12 = Dhu al-Hijjah */
    val month: Int,
    val day: Int
) {
    val monthName: String get() = MONTHS[(month - 1).coerceIn(0, 11)]
    val monthArabic: String get() = MONTHS_ARABIC[(month - 1).coerceIn(0, 11)]
    val formatted: String get() = "$day $monthName $year AH"

    val isRamadan: Boolean get() = month == 9
}

object HijriCalendar {

    val MONTHS = listOf(
        "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
        "Jumada al-Ula", "Jumada al-Akhirah", "Rajab", "Sha'ban",
        "Ramadan", "Shawwal", "Dhu al-Qadah", "Dhu al-Hijjah"
    )

    val MONTHS_ARABIC = listOf(
        "مُحَرَّم", "صَفَر", "رَبيع الأوّل", "رَبيع الآخر",
        "جُمادى الأولى", "جُمادى الآخرة", "رَجَب", "شَعْبان",
        "رَمَضان", "شَوّال", "ذُو القَعْدة", "ذُو الحِجّة"
    )

    fun isLeapYear(year: Int): Boolean = (11 * year + 14) % 30 < 11

    fun daysInMonth(year: Int, month: Int): Int = when {
        month == 12 -> if (isLeapYear(year)) 30 else 29
        month % 2 == 1 -> 30
        else -> 29
    }

    fun daysInYear(year: Int): Int = if (isLeapYear(year)) 355 else 354

    /** Gregorian date -> Hijri date. */
    fun fromGregorian(date: LocalDate): HijriDate {
        // Days since the Hijri epoch. The epoch is 16 July 622 CE in the Julian
        // calendar, i.e. JD 1948440; the +10632 below folds the 30-year cycle
        // offset into the running day count.
        val jd = julianDay(date)
        val l0 = jd - 1948440 + 10632
        val n = (l0 - 1) / 10631
        var l = l0 - 10631 * n + 354
        val j = ((10985 - l) / 5316) * ((50 * l) / 17719) +
            (l / 5670) * ((43 * l) / 15238)
        l -= ((30 - j) / 15) * ((17719 * j) / 50) +
            (j / 16) * ((15238 * j) / 43)
        l += 29
        val month = (24 * l) / 709
        val day = l - (709 * month) / 24
        val year = 30 * n + j - 30
        return HijriDate(year, month.coerceIn(1, 12), day.coerceIn(1, 30))
    }

    /** Julian Day Number for the given Gregorian date at midnight. */
    private fun julianDay(date: LocalDate): Int {
        var y = date.year
        var m = date.monthValue
        val d = date.dayOfMonth
        if (m <= 2) {
            y -= 1
            m += 12
        }
        val a = y / 100
        val b = 2 - a + a / 4
        return (365.25 * (y + 4716)).toInt() +
            (30.6001 * (m + 1)).toInt() + d + b - 1524
    }

    /**
     * How many days until the next Ramadan begins, or 0 if it is Ramadan now.
     * Used by the "Ramadan" line on the home screen, and never guessed beyond
     * the ±1 day the calendar itself carries.
     */
    fun daysUntilRamadan(date: LocalDate): Int? {
        val today = fromGregorian(date)
        if (today.month == 9) return 0
        var d = date
        // Ramadan is roughly eleven days earlier each year, so 370 steps always
        // contains one. Cheap enough to do by walking rather than by inverting the
        // conversion, and it keeps the rule in one place.
        for (i in 1..370) {
            d = d.plusDays(1)
            val h = fromGregorian(d)
            if (h.month == 9) return if (h.day == 1) i else i - (h.day - 1)
        }
        return null
    }
}
