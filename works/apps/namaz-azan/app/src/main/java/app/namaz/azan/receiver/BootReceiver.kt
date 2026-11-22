package app.namaz.azan.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import app.namaz.azan.data.AzanScheduler
import app.namaz.azan.data.NotificationHelper
import app.namaz.azan.data.Settings

/**
 * Alarms do not survive a reboot or a time-zone change, so re-arm them here.
 */
class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_TIME_CHANGED,
            Intent.ACTION_TIMEZONE_CHANGED -> {
                val settings = Settings(context)
                NotificationHelper.ensureChannels(context, settings.azanSoundEnabled)
                AzanScheduler.scheduleNext(context, settings)
            }
        }
    }
}
