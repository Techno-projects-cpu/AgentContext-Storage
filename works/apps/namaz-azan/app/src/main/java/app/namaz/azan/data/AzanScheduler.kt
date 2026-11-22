package app.namaz.azan.data

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import app.namaz.azan.core.Prayer
import app.namaz.azan.core.PrayerCalculator
import app.namaz.azan.core.PrayerTime
import app.namaz.azan.receiver.AzanAlarmReceiver
import java.time.Instant

/**
 * Schedules the azan.
 *
 * Strategy: rather than registering every prayer months ahead (which drifts and costs
 * battery), the app keeps exactly one pending alarm for the *next* prayer that has azan
 * enabled. When that alarm fires, the receiver calls [scheduleNext] again. Alarms are
 * re-armed on boot, on time change and whenever the user changes a setting.
 */
object AzanScheduler {

    private const val REQUEST_CODE = 4242

    private fun pending(context: Context, prayer: Prayer, timeLabel: String): PendingIntent {
        val intent = Intent(context, AzanAlarmReceiver::class.java).apply {
            putExtra(AzanAlarmReceiver.EXTRA_PRAYER, prayer.name)
            putExtra(AzanAlarmReceiver.EXTRA_TIME, timeLabel)
        }
        return PendingIntent.getBroadcast(
            context,
            REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    fun canScheduleExact(context: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true
        val manager = context.getSystemService(AlarmManager::class.java) ?: return false
        return manager.canScheduleExactAlarms()
    }

    /** Find and arm the next azan. Returns the prayer that was scheduled, if any. */
    fun scheduleNext(context: Context, settings: Settings, now: Instant = Instant.now()): PrayerTime? {
        val prayerTime = nextAzan(settings, now) ?: run {
            cancel(context)
            return null
        }
        NotificationHelper.ensureChannels(context, settings.azanSoundEnabled)

        val manager = context.getSystemService(AlarmManager::class.java) ?: return prayerTime
        val pendingIntent = pending(context, prayerTime.prayer, formatTime(prayerTime))

        if (canScheduleExact(context)) {
            manager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP, prayerTime.instant.toEpochMilli(), pendingIntent
            )
        } else {
            // Without the exact-alarm permission Android may deliver this late, but it
            // still fires, which beats no reminder at all.
            manager.setAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP, prayerTime.instant.toEpochMilli(), pendingIntent
            )
        }
        return prayerTime
    }

    fun cancel(context: Context) {
        val manager = context.getSystemService(AlarmManager::class.java) ?: return
        val intent = Intent(context, AzanAlarmReceiver::class.java)
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        manager.cancel(pendingIntent)
        pendingIntent.cancel()
    }

    /**
     * The next prayer with azan enabled, searching today then tomorrow so a late-night
     * refresh still finds Fajr.
     */
    fun nextAzan(settings: Settings, now: Instant): PrayerTime? {
        val zone = settings.zone()
        val method = settings.method()
        val madhab = settings.madhab()
        val adjustments = settings.adjustments()
        val latitude = settings.latitude
        val longitude = settings.longitude

        val today = now.atZone(zone).toLocalDate()
        for (offset in 0L..1L) {
            val date = today.plusDays(offset)
            val day = PrayerCalculator.forDate(
                date, latitude, longitude, zone, method, madhab, adjustments
            )
            day.times
                .filter { it.prayer != Prayer.SUNRISE && settings.azanEnabled(it.prayer) }
                .firstOrNull { it.instant.isAfter(now) }
                ?.let { return it }
        }
        return null
    }

    fun formatTime(time: PrayerTime): String = time.time.toString().take(5)
}
