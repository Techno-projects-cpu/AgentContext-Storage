package app.namaz.azan.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.namaz.azan.ui.theme.SkyInk
import app.namaz.azan.ui.theme.SkyPalette
import app.namaz.azan.ui.theme.SunGold
import kotlin.math.PI
import kotlin.math.sin

/**
 * The opening screen.
 *
 * Why Bismillah and not a spinner: this app has one purpose, and the sentence that
 * opens every surah of the Qur'an except one is the right thing to meet somebody
 * with. It is not decoration laid over a delay — the screen exists for exactly as
 * long as it takes the app to work out today's times, which is real work, and the
 * sentence gives that moment a meaning instead of a spinning circle.
 *
 * Timings, and why:
 *
 *   - 0 ms: the ground fades up from black, 700 ms.
 *   - 250 ms: the ornament draws itself from the centre outward, 1100 ms, with the
 *     stroke arriving as a light rather than as a line.
 *   - 700 ms: the Arabic settles in, 900 ms, rising 14 dp.
 *   - 1050 ms: the transliteration and the English, 800 ms.
 *   - 1900 ms: the whole screen cross-fades to the sky, 600 ms.
 *
 * Total 2.5 s, which is about the sum of the work; [onFinished] is also called by
 * the caller's own minimum-hold so the app is never slower than the maths.
 */
@Composable
fun SplashScreen(
    sky: SkyPalette,
    onFinished: () -> Unit
) {
    // One clock drives every beat, so the sequence cannot drift apart.
    val clock = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        clock.animateTo(1f, tween(Splash.DURATION_MS, easing = LinearEasing))
        onFinished()
    }

    fun beat(startMs: Int, lengthMs: Int): Float =
        (((clock.value * Splash.DURATION_MS) - startMs) / lengthMs).coerceIn(0f, 1f)

    val groundAlpha = beat(0, 700)
    val ornament = beat(250, 1100)
    val arabicIn = beat(700, 900)
    val latinIn = beat(1050, 800)
    val exit = beat(1900, 600)

    // A very slow breath on the whole composition, so the screen is never quite
    // still — a still frame on a phone reads as a hung app.
    val breath = 0.5f + 0.5f * sin(clock.value * PI.toFloat() * 2f)

    Box(
        Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    0f to Color(0xFF07090F),
                    0.55f to Color(0xFF0B1020),
                    1f to blend(Color(0xFF07090F), sky.ground, 0.35f)
                )
            )
    ) {
        // The sky itself, only at the very end, so the handover is a sunrise rather
        // than a cut to a different screen.
        if (exit > 0f) {
            Box(Modifier.fillMaxSize()) {
                SkyCanvas(
                    palette = sky,
                    sunAltitude = -18.0,
                    sunAzimuth = 90.0,
                    modifier = Modifier.fillMaxSize(),
                    animate = false
                )
            }
            Box(
                Modifier
                    .fillMaxSize()
                    .background(Color(0xFF07090F).copy(alpha = 1f - exit))
            )
        } else {
            Box(
                Modifier
                    .fillMaxSize()
                    .background(Color(0xFF07090F).copy(alpha = 1f - groundAlpha * 0.86f))
            )
        }

        Column(
            Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // The ornament: one continuous stroke, a shallow arc with a bead at its
            // centre. Drawn, not placed, so it arrives as calligraphy would.
            // fillMaxWidth, not fillMaxSize: filling both axes and then setting a
            // height contradicts itself, and the canvas ends up as tall as the
            // screen with the arc drawn in a 64 dp band at the top of it.
            Canvas(
                Modifier
                    .fillMaxWidth(0.72f)
                    .height(76.dp)
            ) {
                drawOrnament(
                    progress = ornament,
                    alpha = (1f - exit) * (0.55f + 0.45f * ornament),
                    glow = 0.90f + 0.10f * breath
                )
            }

            Spacer(Modifier.height(34.dp))

            // Arabic. Rendered at a size that gives the script room, because a
            // calligraphic line set small reads as a label.
            Text(
                text = "بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                color = SunGold.copy(alpha = arabicIn),
                fontSize = 31.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .padding(horizontal = 24.dp)
                    .offset(y = ((1f - arabicIn) * 14f).dp)
            )

            Spacer(Modifier.height(26.dp))

            Text(
                text = "Bismillāhir-Raḥmānir-Raḥīm",
                color = SkyInk.copy(alpha = latinIn * 0.86f),
                fontSize = 14.sp,
                letterSpacing = 1.6.sp,
                fontWeight = FontWeight.Light,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(8.dp))

            Text(
                text = "In the name of God, the Most Compassionate, the Most Merciful",
                color = SkyInk.copy(alpha = latinIn * 0.46f),
                fontSize = 11.sp,
                letterSpacing = 0.3.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 40.dp)
            )
        }

        // A hairline that fills left to right over the whole splash: the one piece
        // of "loading" grammar on the screen, and it costs nothing.
        Box(
            Modifier
                .fillMaxSize()
                .padding(bottom = 44.dp),
            contentAlignment = Alignment.BottomCenter
        ) {
            Canvas(Modifier.fillMaxSize()) {
                val y = size.height
                val w = size.width
                val inset = w * 0.30f
                drawLine(
                    color = Color.White.copy(alpha = 0.10f * (1f - exit)),
                    start = Offset(inset, y),
                    end = Offset(w - inset, y),
                    strokeWidth = 1.2f * density
                )
                drawLine(
                    color = SunGold.copy(alpha = 0.55f * (1f - exit)),
                    start = Offset(inset, y),
                    end = Offset(inset + (w - inset * 2) * clock.value, y),
                    strokeWidth = 1.2f * density
                )
            }
        }
    }
}

object Splash {
    const val DURATION_MS = 2500
}

/**
 * The ornament: a shallow arc, widest in the middle, with a small lozenge at the
 * centre and tapering ends.
 *
 * Drawn from the centre outward as [progress] rises, which is the direction a pen
 * would move and the reason it reads as written rather than as revealed.
 */
private fun DrawScope.drawOrnament(progress: Float, alpha: Float, glow: Float) {
    if (progress <= 0f) return
    val w = size.width
    val h = size.height
    val cx = w / 2f
    val cy = h / 2f
    val half = (w * 0.30f) * progress

    // the arc
    val path = Path().apply {
        moveTo(cx - half, cy + h * 0.16f)
        quadraticTo(cx, cy - h * 0.34f, cx + half, cy + h * 0.16f)
    }
    // glow first, then the line: the same trick a light source needs
    drawPath(path, SunGold.copy(alpha = alpha * 0.16f * glow), style = Stroke(width = 7f * density))
    drawPath(path, SunGold.copy(alpha = alpha * 0.34f), style = Stroke(width = 3f * density))
    drawPath(path, SunGold.copy(alpha = alpha * 0.92f), style = Stroke(width = 1.2f * density))

    // the lozenge at the centre, which only appears once the arc has grown past it
    if (progress > 0.35f) {
        val t = ((progress - 0.35f) / 0.65f).coerceIn(0f, 1f)
        val r = 5.5f * density * t
        val lozenge = Path().apply {
            moveTo(cx, cy - r * 1.8f)
            lineTo(cx + r, cy)
            lineTo(cx, cy + r * 1.8f)
            lineTo(cx - r, cy)
            close()
        }
        drawPath(lozenge, SunGold.copy(alpha = alpha * 0.95f))
    }

    // two dots, one either side, arriving last
    if (progress > 0.7f) {
        val t = ((progress - 0.7f) / 0.3f).coerceIn(0f, 1f)
        listOf(cx - half * 0.62f, cx + half * 0.62f).forEach { x ->
            drawCircle(
                SunGold.copy(alpha = alpha * 0.60f * t),
                radius = 2.2f * density * t,
                center = Offset(x, cy - h * 0.16f)
            )
        }
    }
}

/** Linear blend of two colours, for the last frame of the handover. */
private fun blend(a: Color, b: Color, t: Float): Color = Color(
    red = a.red + (b.red - a.red) * t,
    green = a.green + (b.green - a.green) * t,
    blue = a.blue + (b.blue - a.blue) * t
)
