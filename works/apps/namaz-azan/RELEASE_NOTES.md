## Namaz & Azan 1.0.0

Offline prayer times and azan reminders for Android. Kotlin + Jetpack Compose.

**Download `namaz-azan-1.0.0.apk` and open it on your phone.** Android asks you to allow
installing from this source the first time.

### What's in it

Five prayers plus sunrise with a live countdown · azan at each prayer, switchable per
prayer · full-screen azan over the lock screen · alarms re-armed after reboot and
timezone change · 16 preset cities (Guntur default) or device GPS · 9 calculation
methods · Shafi/Hanafi Asr · ±15 min per-prayer adjustment · Material 3 light/dark.

Fully offline — no network, no account, no ads, no analytics. Location never leaves
the phone.

### Prayer time accuracy

The astronomy is a port of the Adhan/Meeus solar algorithm. It was re-implemented and
diffed against an independent reference library at 4 cities × 4 dates before any Kotlin
was written: **worst deviation 58 seconds**. CI re-checks it on every push with 11 unit
tests, including a year-long stability sweep.

Guntur, 22 November 2026 (Karachi method, Shafi Asr):

| Fajr | Sunrise | Dhuhr | Asr | Maghrib | Isha |
|---|---|---|---|---|---|
| 05:00 | 06:15 | 11:55 | 15:09 | 17:33 | 18:49 |

### Requirements

Android 8.0 (API 26) or newer.

Signed with a throwaway key generated inside CI so it installs directly. That is **not**
a Play Store upload key — see `README.md` for generating your own.

### Notes

No adhan recitation is bundled (a synthesized chime plays); adding one means dropping a
licensed recording into `res/raw/`. Not on Play: a new personal account needs 12 testers
for 14 continuous days before production access.

SHA-256 of the APK:

```
0394535c1a767eb3d1c940d3cb1147c1d7bb103b2c71afff9e6685417bbbab26
```
