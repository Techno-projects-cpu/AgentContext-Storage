package app.namaz.azan.data

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import app.namaz.azan.R
import app.namaz.azan.core.Prayer
import app.namaz.azan.ui.AzanActivity
import app.namaz.azan.ui.MainActivity

object NotificationHelper {

    const val CHANNEL_AZAN = "azan"
    const val CHANNEL_REMINDER = "reminder"

    /** Create channels and re-point the azan channel at the bundled tone. */
    fun ensureChannels(context: Context, withSound: Boolean) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(NotificationManager::class.java) ?: return

        // The azan channel is deleted first so that changing the sound setting actually
        // takes effect: Android ignores sound changes on an existing channel.
        manager.deleteNotificationChannel(CHANNEL_AZAN)

        val azan = NotificationChannel(
            CHANNEL_AZAN,
            context.getString(R.string.channel_azan),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = context.getString(R.string.channel_azan_desc)
            enableVibration(true)
            setBypassDnd(true)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            if (withSound) {
                val sound = Uri.parse("android.resource://${context.packageName}/${R.raw.azan_chime}")
                setSound(
                    sound,
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build()
                )
            } else {
                setSound(null, null)
            }
        }
        manager.createNotificationChannel(azan)

        val reminder = NotificationChannel(
            CHANNEL_REMINDER,
            context.getString(R.string.channel_reminder),
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply { description = context.getString(R.string.channel_reminder_desc) }
        manager.createNotificationChannel(reminder)
    }

    /** The reminder that fires at the prayer time. */
    fun azanNotification(
        context: Context,
        prayer: Prayer,
        timeLabel: String,
        withSound: Boolean
    ): Notification {
        val fullScreen = Intent(context, AzanActivity::class.java).apply {
            putExtra(AzanActivity.EXTRA_PRAYER, prayer.name)
            putExtra(AzanActivity.EXTRA_TIME, timeLabel)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        }
        val fullScreenPending = PendingIntent.getActivity(
            context,
            prayer.ordinal + 100,
            fullScreen,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val openApp = PendingIntent.getActivity(
            context,
            prayer.ordinal + 200,
            Intent(context, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(context, CHANNEL_AZAN)
            .setSmallIcon(R.drawable.ic_mosque)
            .setContentTitle(context.getString(R.string.azan_title, prayer.label))
            .setContentText(context.getString(R.string.azan_body))
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setAutoCancel(true)
            .setContentIntent(openApp)
            .setFullScreenIntent(fullScreenPending, true)
            .setStyle(NotificationCompat.BigTextStyle().bigText(context.getString(R.string.azan_body)))
            .setWhen(System.currentTimeMillis())
            .setShowWhen(true)
            .build()
    }

    fun notify(context: Context, id: Int, notification: Notification) {
        val manager = context.getSystemService(NotificationManager::class.java) ?: return
        manager.notify(id, notification)
    }
}
