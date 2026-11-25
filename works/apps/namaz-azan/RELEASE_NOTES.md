## Namaz & Azan 1.1.0

Offline prayer times and azan reminders for Android. Kotlin + Jetpack Compose.

**Download `namaz-azan-1.1.0.apk` and open it on your phone.** Android asks you to allow
installing from this source the first time.

### What's new in 1.1

**The screen is the sky.** The whole background is a live gradient driven by the sun's
real altitude above *your* horizon — orange at Maghrib, violet at Isha, near-black with
stars after that, deep blue at noon. Nothing is a time-of-day lookup: the app solves the
sun's position every second, so the same app is a different colour in Delhi and in Oslo.

**More of the day, and more of the year:**

| New | What it does |
|---|---|
| Night panel | Imsak, Islamic midnight, and the last third — the three times that divide the night, matching the reference to the minute (04:45 / 23:52 / 01:58 for Guntur on 9 Nov 2026) |
| The week | Seven days of sunrise and sunset, with a day-length bar so the season is visible at a glance |
| The year | Today's daylight, how fast it is changing over the week, and a countdown to Ramadan |
| Month timetable | The full month, Fajr to Isha, with the Hijri day in the margin — the sheet a mosque puts on the wall, computed for your coordinates |
| Qibla | The bearing to the Kaaba on a true-north compass rose (Guntur 284.1°) |

### Accuracy, and one deliberate limitation

Two real bugs were found and fixed by diffing against a reference API:

1. **Dhuhr was systematically 1–2 minutes late.** The app applied a one-minute guard
   after solar noon *and* then rounded up again. True solar noon in Guntur on
   9 Nov 2026 is 11:52:03 (confirmed by two independent sources); the app now applies
   the guard once and rounds once.
2. **Umm al-Qura Isha was 30 minutes short during Ramadan.** The published rule is 90
   minutes after Maghrib, extended to **120 minutes in Ramadan**. Verified against
   Makkah, 13 Ramadan 1448: Maghrib 18:21, Isha 20:21.

The Hijri date uses the arithmetic Islamic calendar, which is at most **±1 day** from the
Umm al-Qura table (agreement at 2 of 4 checked dates, one day early at the other two).
That is exact for Ramadan timing only to the day, so the app shows the date it is using
and says to confirm with your mosque. This is stated in the app, not just here.

Everything else was re-verified after the rewrite: Guntur, Oslo in polar night (the
high-latitude fallback matches), Sydney in the southern-hemisphere winter, and Makkah.

### Accessibility

Text contrast was measured rather than eyeballed: the sky keeps its colour up top and
deepens toward the bottom of the screen, because dark ink on a lit sunset sky is 1.67:1
— far below the 4.5:1 body text needs. With the ground deepening and cards derived from
it, the worst contrast anywhere in the day is **6.9:1**. A unit test asserts this across
every sun altitude from −25° to +60°, so a future palette change cannot quietly break it.

### What was already there

Five prayers plus sunrise with a live countdown · azan at each prayer, switchable per
prayer · full-screen azan over the lock screen · alarms re-armed after reboot and timezone
change · 16 preset cities (Guntur default) or device GPS · 9 calculation methods ·
Shafi/Hanafi Asr · ±15 min per-prayer adjustment.

### The promise, unchanged

Fully offline — no network permission in the manifest, no account, no ads, no analytics,
no third-party SDKs. Location never leaves the phone. The only two permissions are
location (optional, for your own coordinates) and notifications.

### Requirements

Android 8.0 (API 26) or newer.

Signed with a throwaway key generated inside CI so it installs directly. That is **not**
a Play Store upload key — see `README.md` for generating your own.

### Notes

No adhan recitation is bundled (a synthesized chime plays); adding one means dropping a
licensed recording into `res/raw/`. Not on Play: a new personal account needs 12 testers
for 14 continuous days before production access.
