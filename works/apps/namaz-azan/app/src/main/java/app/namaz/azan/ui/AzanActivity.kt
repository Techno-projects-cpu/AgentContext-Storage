package app.namaz.azan.ui

import android.app.KeyguardManager
import android.media.MediaPlayer
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.namaz.azan.R
import app.namaz.azan.core.Prayer
import app.namaz.azan.data.Settings
import app.namaz.azan.ui.theme.NamazTheme

/**
 * Full-screen azan: shows over the lock screen, plays the tone, and stops as soon as
 * the user acknowledges it.
 */
class AzanActivity : ComponentActivity() {

    private var player: MediaPlayer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            (getSystemService(KeyguardManager::class.java))?.requestDismissKeyguard(this, null)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
            )
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val prayerName = intent.getStringExtra(EXTRA_PRAYER)
        val prayer = Prayer.entries.firstOrNull { it.name == prayerName } ?: Prayer.FAJR
        val timeLabel = intent.getStringExtra(EXTRA_TIME).orEmpty()

        val settings = Settings(this)
        if (settings.azanSoundEnabled) playTone()

        setContent {
            NamazTheme {
                AzanScreen(
                    prayer = prayer,
                    timeLabel = timeLabel,
                    onDismiss = { finish() }
                )
            }
        }
    }

    private fun playTone() {
        player = MediaPlayer.create(this, R.raw.azan_chime)?.apply {
            isLooping = false
            setOnCompletionListener { finish() }
            start()
        }
    }

    override fun onDestroy() {
        player?.release()
        player = null
        super.onDestroy()
    }

    companion object {
        const val EXTRA_PRAYER = "prayer"
        const val EXTRA_TIME = "time"
    }
}

@Composable
private fun AzanScreen(prayer: Prayer, timeLabel: String, onDismiss: () -> Unit) {
    Column(
        Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(Color(0xFF0B3D2E), Color(0xFF071F18))
                )
            )
            .padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            "حَيَّ عَلَى الصَّلَاة",
            style = MaterialTheme.typography.headlineMedium,
            color = Color(0xFFD4AF37),
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(28.dp))
        Text(
            prayer.arabic,
            fontSize = 56.sp,
            color = Color.White,
            fontWeight = FontWeight.Light
        )
        Spacer(Modifier.height(8.dp))
        Text(
            "It is time for ${prayer.label}",
            style = MaterialTheme.typography.headlineSmall,
            color = Color.White
        )
        if (timeLabel.isNotBlank()) {
            Text(
                timeLabel,
                style = MaterialTheme.typography.titleLarge,
                color = Color.White.copy(alpha = 0.7f)
            )
        }
        Spacer(Modifier.height(48.dp))
        Button(onClick = onDismiss) { Text("Stop azan") }
    }
}
