# Namaz & Azan — Android app

A prayer-time and azan reminder app for Android, written in Kotlin + Jetpack Compose.
Everything is computed on the device: **no network, no accounts, no ads, no analytics,
and no location ever leaves the phone.**

## What it looks like

The whole screen is the sky. The background gradient is computed from the sun's **real
altitude above your horizon**, so the app is orange at Maghrib in Guntur and daylight
blue at the same clock time in London. Nothing is a time-of-day lookup table; the sun is
solved every second from your coordinates.

Text contrast was measured, not eyeballed. Dark ink on a lit sunset sky is only **1.67:1**,
so the sky keeps its colour at the top of the screen and deepens toward the bottom, and
cards are derived from that ground. The worst contrast anywhere in the day is **6.9:1**,
and a unit test asserts it at every sun altitude from −25° to +60°.

## What it does

- **Today**: five prayers plus sunrise, a live countdown, and an arc showing how far
  through the current prayer window you are
- **The night**: Imsak, Islamic midnight and the last third of the night (tahajjud)
- **The week**: seven days of sunrise and sunset, with day-length bars
- **The year**: today's daylight, how fast it is changing, and a countdown to Ramadan
- **The month**: a full timetable, Fajr to Isha, with the Hijri day in the margin
- **Qibla**: the great-circle bearing to the Kaaba on a true-north compass rose
- Azan at each prayer time, with a per-prayer on/off switch
- Full-screen azan that shows over the lock screen and plays a tone
- Automatic re-arming after reboot or a time-zone change
- Sixteen preset cities (Guntur default) or the device's own location
- Nine calculation methods and both Asr conventions (Shafi 1× / Hanafi 2×)
- Per-prayer manual adjustment, ±15 min, for matching your local mosque

## Two things it deliberately does not pretend

**The Hijri date is arithmetic, not observed.** It uses the tabular Islamic calendar,
which is at most ±1 day from the Umm al-Qura table (it agreed outright at 2 of 4 dates
checked, and was one day early at the other two). It is not the sighting in your city.
The app therefore shows the date it is using and tells you to confirm with your mosque.
Everything that depends on it — the Ramadan Isha interval — inherits that ±1 day.

**The qibla bearing is to true north.** Magnetic declination is not applied, because
doing so from a coarse world model would be worse than saying plainly which north is
which. The screen says "from true north" and tells you to allow for declination.

## Prayer time accuracy

The astronomy is a port of the classical solar algorithm used by the well-known
Adhan-compatible libraries — Meeus, *Astronomical Algorithms*, chapters 12, 22, 25, 102.
It is not an approximation or a lookup table.

It was validated against an independent reference implementation across four cities
and four dates: **worst deviation of any prayer: 58 seconds**, i.e. every prayer lands
within one minute. The unit tests in `app/src/test` pin the results to the minute so a
future change cannot silently drift.

Two errors were found and fixed in 1.1 by diffing against that reference:

- **Dhuhr was 1–2 minutes late.** The one-minute guard after solar noon was being
  followed by a second round-up on display. True solar noon in Guntur on 9 Nov 2026 is
  11:52:03 (confirmed independently by two sources).
- **Umm al-Qura and Qatar Isha were 30 minutes short in Ramadan.** The published rule is
  90 minutes after Maghrib, extended to 120 in Ramadan. Verified against Makkah,
  13 Ramadan 1448: Maghrib 18:21, Isha 20:21.

Re-verified after the rewrite at Guntur, Oslo in polar night (the high-latitude fallback
matches), Sydney in the southern winter, and Makkah.

`tools/ref.py` is a line-for-line Python port of the Kotlin astronomy. There is no JDK in
the authoring environment, so this is how the numbers were diffed without one — and it is
kept in step with the app so a future diff is honest.

No app like this should be trusted blindly: always confirm with your local mosque,
and use the manual adjustment if your mosque differs by a few minutes.

## Getting the APK

The APK is built by GitHub Actions, because the build needs an Android SDK.

1. Open the **Actions** tab of this repository
2. Pick the newest **Build Namaz & Azan APK** run
3. Download the **namaz-azan-apk** artifact (a zip containing the `.apk`)
4. Copy the `.apk` to your phone and open it — allow "install unknown apps" when asked

The artifact is signed with a throwaway key generated inside the build, so it installs
directly. That key is **not** a Play Store upload key: for Play you must generate and
keep your own keystore (see below).

## Building it yourself

You need Android Studio (or a JDK 17 + Android SDK). Then:

```bash
cd works/apps/namaz-azan
gradle testDebugUnitTest    # prayer-time accuracy tests
gradle assembleDebug        # app/build/outputs/apk/debug/
```

Opening the folder in Android Studio and pressing Run does the same thing.

### Play Store release

Generate a keystore once and keep it safe — losing it means you can never update the app:

```bash
keytool -genkeypair -keystore namaz-upload.jks -alias namaz \
  -keyalg RSA -keysize 2048 -validity 10000
```

Then set `NAMAZ_KEYSTORE`, `NAMAZ_STORE_PASSWORD`, `NAMAZ_KEY_ALIAS` and
`NAMAZ_KEY_PASSWORD` for the build; `app/build.gradle.kts` picks them up.

Remember that a **new personal Play account needs 12 testers for 14 continuous days**
before production access is granted.

## Notable implementation details

| concern | approach |
|---|---|
| battery | exactly one pending alarm exists at a time (the next azan), re-armed when it fires |
| alarm latency | `setExactAndAllowWhileIdle` when permitted, otherwise `setAndAllowWhileIdle` plus an in-app prompt |
| notification sound | the azan channel is deleted and recreated when the sound setting changes, since Android ignores sound edits on an existing channel |
| reboot | a `BOOT_COMPLETED` / `TIME_SET` / `TIMEZONE_CHANGED` receiver re-arms the alarm |
| high latitudes | Fajr/Isha fall back to a fraction of the night when the sun never reaches the required angle, instead of producing NaN |
| dependencies | no Room, no Hilt, no Retrofit — fewer moving parts, smaller APK, nothing to fail in CI |

## Layout

```
app/src/main/java/app/namaz/azan/
  core/       Astronomy.kt (solar position), PrayerCalculator.kt (methods, madhabs)
  data/       Settings.kt, AzanScheduler.kt, NotificationHelper.kt, LocationHelper.kt
  receiver/   AzanAlarmReceiver.kt, BootReceiver.kt
  ui/         MainActivity, HomeScreen, SettingsScreen, AzanActivity, theme/
app/src/test/ PrayerTimesTest.kt
```

## Licence

The astronomy follows the MIT-licensed Adhan algorithm family; Meeus is a published
reference. This app's own code is free to reuse.
