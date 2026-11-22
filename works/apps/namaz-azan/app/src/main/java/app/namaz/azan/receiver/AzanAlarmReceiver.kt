package app.namaz.azan.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationManagerCompat
import app.namaz.azan.core.Prayer
import app.namaz.azan.data.AzanScheduler
import app.namaz.azan.data.NotificationHelper
import app.namaz.azan.data.Settings

/** Fires at the prayer time, shows the azan, then arms the following prayer. */
class AzanAlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val settings = Settings(context)
        val prayerName = intent.getStringExtra(EXTRA_PRAYER)
        val prayer = Prayer.entries.firstOrNull { it.name == prayerName } ?: return
        val timeLabel = intent.getStringExtra(EXTRA_TIME) ?: ""

        NotificationHelper.ensureChannels(context, settings.azanSoundEnabled)

        if (NotificationManagerCompat.from(context).areNotificationsEnabled()) {
            NotificationHelper.notify(
                context,
                AZAN_NOTIFICATION_ID,
                NotificationHelper.azanNotification(context, prayer, timeLabel, settings.azanSoundEnabled)
            )
        }

        // Arm the next one immediately; a receiver has a short window, so this is cheap.
        AzanScheduler.scheduleNext(context, settings)
    }

    companion object {
        const val EXTRA_PRAYER = "prayer"
        const val EXTRA_TIME = "time"
        const val AZAN_NOTIFICATION_ID = 1001
    }
}
