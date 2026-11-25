package app.namaz.azan.ui

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import app.namaz.azan.ui.theme.SkyPalette
import app.namaz.azan.ui.theme.hairline
import app.namaz.azan.ui.theme.isNight
import app.namaz.azan.ui.theme.sunDiscColor
import app.namaz.azan.ui.theme.sunDiscRadius
import app.namaz.azan.ui.theme.sunDiscCentreY
import app.namaz.azan.ui.theme.sunGlowCentreY
import app.namaz.azan.ui.theme.sunGlowRadiusFraction
import app.namaz.azan.ui.theme.sunGlowStrength
import kotlin.math.cos
import kotlin.math.sin

/**
 * The sky, drawn.
 *
 * Four layers, in the order they exist in a real sky:
 *
 *   1. the four-stop vertical gradient
 *   2. the sun's bloom — a wide wash, flattened vertically so it reads as haze on
 *      the horizon rather than a spotlight
 *   3. the sun or moon
 *   4. stars, and only once the sun is properly down
 *
 * Everything is a pure function of (sun altitude, sun azimuth, canvas size), so
 * the sky can be drawn at any size and never needs a bitmap.
 */
@Composable
fun SkyCanvas(
    palette: SkyPalette,
    sunAltitude: Double,
    sunAzimuth: Double,
    modifier: Modifier = Modifier,
    animate: Boolean = true
) {
    // Two slow, independent motions, both far too gentle to notice directly:
    //
    //   - the gradient drifts a few percent over 36 seconds, which is what stops a
    //     static gradient from looking like a screenshot on a phone that is on a
    //     desk in front of you;
    //   - the stars twinkle through a 4-second breath, offset per star so the field
    //     never pulses in unison.
    //
    // Both are derived from one infinite clock, so they cost one animation, not two.
    val drift = if (!animate) 0f else {
        val transition = rememberInfiniteTransition(label = "sky")
        val v by transition.animateFloat(
            initialValue = 0f,
            targetValue = 1f,
            animationSpec = infiniteRepeatable(
                animation = tween(36_000, easing = LinearEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "drift"
        )
        v
    }
    val twinkle = if (!animate) 0.5f else {
        val transition = rememberInfiniteTransition(label = "twinkle")
        val v by transition.animateFloat(
            initialValue = 0f,
            targetValue = 1f,
            animationSpec = infiniteRepeatable(
                animation = tween(4_000, easing = FastOutSlowInEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "twinkle"
        )
        v
    }

    // The palette itself is animated between sun positions, so the moment the sun
    // drops past a band boundary the screen dissolves rather than steps. 1.6 s is
    // long enough to read as light changing and short enough not to lag the clock.
    val animatedZenith by animateColorAsState(palette.zenith, tween(1600), label = "zenith")
    val animatedMid by animateColorAsState(palette.mid, tween(1600), label = "mid")
    val animatedBand by animateColorAsState(palette.band, tween(1600), label = "band")
    val animatedGround by animateColorAsState(palette.ground, tween(1600), label = "ground")
    val animatedNight by animateFloatAsState(palette.night, tween(1600), label = "night")
    val shown = palette.copy(
        zenith = animatedZenith,
        mid = animatedMid,
        band = animatedBand,
        ground = animatedGround,
        night = animatedNight
    )

    Canvas(modifier) {
        drawSky(shown, sunAltitude, sunAzimuth, size, drift, twinkle)
    }
}

fun DrawScope.drawSky(
    palette: SkyPalette,
    sunAltitude: Double,
    sunAzimuth: Double,
    size: Size,
    drift: Float = 0f,
    twinkle: Float = 0.5f
) {
    val w = size.width
    val h = size.height

    // 1. the gradient. Four stops, at the fractions the render proved: the warm
    //    band needs its own stop or it drowns between the blue and the ground.
    //
    //    The stops breathe by up to 1.7% of the height. At this amplitude it is
    //    invisible as motion and visible as life; anything larger reads as the
    //    screen sliding, which is a bug, not an effect.
    val breathe = 0.017f * (drift - 0.5f)
    drawRect(
        brush = Brush.verticalGradient(
            0.00f to palette.zenith,
            (0.38f + breathe) to palette.mid,
            (0.66f + breathe * 0.6f) to palette.band,
            1.00f to palette.ground,
            startY = 0f,
            endY = h
        )
    )

    val cx = w * azimuthToX(sunAzimuth)
    // Two centres: the glow sits on the horizon band, the disc sits up in the sky
    // where a light source belongs and where no card can cover it.
    val glowY = h * sunGlowCentreY(sunAltitude)
    val discY = h * sunDiscCentreY(sunAltitude)

    // 2. the bloom, flattened vertically. Tall bloom = spotlight; flat = weather.
    val glow = sunGlowStrength(sunAltitude)
    if (glow > 0.01f) {
        val rx = w * sunGlowRadiusFraction(sunAltitude)
        val ry = rx * 0.55f
        val warm = if (sunAltitude > 6.0) Color(0xFFFFD9A0) else palette.band
        drawIntoCanvasBloom(warm, glow, cx, glowY, rx, ry)
    }

    // 3. the disc or the moon
    if (!isNight(sunAltitude)) {
        val r = sunDiscRadius(sunAltitude) * density
        val c = sunDiscColor(sunAltitude)
        val centre = Offset(cx, discY)
        // Three rings, each softer than the last outward. The core is drawn at
        // partial alpha at midday: a pure white disc this size on a blue sky
        // reads as a UI element, not as the sun.
        val coreAlpha = (0.55f + 0.40f * ((sunAltitude + 2.0) / 40.0).toFloat().coerceIn(0f, 1f))
        drawCircle(c.copy(alpha = 0.10f), radius = r * 3.0f, center = centre)
        drawCircle(c.copy(alpha = 0.26f), radius = r * 1.7f, center = centre)
        drawCircle(c.copy(alpha = coreAlpha), radius = r, center = centre)
    } else {
        drawMoon(palette, w, h)
    }

    // 4. stars
    val starAlpha = ((-sunAltitude - 4.0) / 14.0).toFloat().coerceIn(0f, 1f)
    if (starAlpha > 0.02f) drawStars(starAlpha, w, h, twinkle)
}

/**
 * A radially-lit wash that is wider than it is tall.
 *
 * Compose's radialGradient is circular, so the ellipse comes from drawing the
 * field into a vertically-scaled region rather than from a gradient parameter.
 */
private fun DrawScope.drawIntoCanvasBloom(
    color: Color,
    strength: Float,
    cx: Float,
    cy: Float,
    rx: Float,
    ry: Float
) {
    // Six concentric passes, each cheap, summing to a smooth falloff. A single
    // circle would band on a large screen; this does not.
    val steps = 6
    for (i in steps downTo 1) {
        val t = i / steps.toFloat()
        val a = strength * 0.16f * (1f - t)
        if (a <= 0.002f) continue
        drawOval(
            brush = Brush.radialGradient(
                0f to color.copy(alpha = a),
                1f to Color.Transparent
            ),
            topLeft = Offset(cx - rx * t, cy - ry * t),
            size = Size(rx * 2f * t, ry * 2f * t)
        )
    }
}

private fun DrawScope.drawMoon(palette: SkyPalette, w: Float, h: Float) {
    val r = 15f * density
    val cx = w * 0.78f
    val cy = h * 0.16f
    val disc = Offset(cx, cy)
    drawCircle(Color(0xFFD6DEEA).copy(alpha = 0.08f), radius = r * 3.0f, center = disc)
    drawCircle(Color(0xFFE8EEF7).copy(alpha = 0.94f), radius = r, center = disc)
    // the crescent: a second disc in the sky's own colour, nudged off-centre
    drawCircle(
        palette.zenith.copy(alpha = 0.94f),
        radius = r * 0.92f,
        center = Offset(cx + r * 0.42f, cy - r * 0.18f)
    )
}

/** Map an azimuth (0 = north, 90 = east) to a horizontal position, 0..1. */
private fun azimuthToX(azimuth: Double): Float {
    // The frame reads east-left / west-right, so sunrise is on one edge and
    // sunset on the other and the screen scans like one day.
    val a = ((azimuth % 360.0) + 360.0) % 360.0
    val east = if (a <= 180.0) a / 180.0 else (360.0 - a) / 180.0
    // Clamped to the middle-right of the frame. A disc at the very edge is half
    // off-screen, and a disc behind the header text is unreadable; both are worse
    // than a disc that sits where the composition wants it.
    return (0.34f + 0.44f * east.toFloat()).coerceIn(0.34f, 0.78f)
}

/**
 * A fixed field of stars. Positions come from a hash of the index, not a random
 * source, so the same stars are in the same places every night — a sky that
 * reshuffles itself looks like noise, not a sky.
 */
private fun DrawScope.drawStars(alpha: Float, w: Float, h: Float, twinkle: Float) {
    for (i in 0 until 90) {
        val fx = hash(i * 7 + 1)
        val fy = hash(i * 13 + 5) * 0.70f      // keep clear of the deep zone
        val bright = 0.25f + 0.75f * hash(i * 31 + 11)
        val r = (0.7f + 1.5f * bright) * density
        val tint = if (fy > 0.45f) Color(0xFFF3E7CE) else Color(0xFFE6EEFB)
        // Each star is at a different point in its own breath, so the field glitters
        // instead of pulsing together like a Christmas tree.
        val phase = hash(i * 53 + 3)
        val breath = 0.72f + 0.28f * kotlin.math.sin(((twinkle + phase) % 1f) * Math.PI.toFloat() * 2f)
        drawCircle(
            tint.copy(alpha = (alpha * bright * 0.9f * breath).coerceIn(0f, 1f)),
            radius = r,
            center = Offset(w * fx, h * fy)
        )
    }
    // three brighter anchors, so the field has hierarchy rather than being a dust
    listOf(0.22f to 0.14f, 0.62f to 0.09f, 0.48f to 0.30f).forEach { (fx, fy) ->
        val c = Offset(w * fx, h * fy)
        val r = 1.9f * density
        drawCircle(Color.White.copy(alpha = alpha * 0.85f), radius = r, center = c)
        drawLine(
            Color.White.copy(alpha = alpha * 0.22f),
            Offset(c.x - r * 3.2f, c.y), Offset(c.x + r * 3.2f, c.y),
            strokeWidth = 0.8f * density
        )
        drawLine(
            Color.White.copy(alpha = alpha * 0.16f),
            Offset(c.x, c.y - r * 3.2f), Offset(c.x, c.y + r * 3.2f),
            strokeWidth = 0.8f * density
        )
    }
}

/** Deterministic 0..1 hash. */
private fun hash(n: Int): Float {
    var x = n * 374761393 + 668265263
    x = (x xor (x shr 13)) * 1274126177
    x = x xor (x shr 16)
    return (x and 0x7FFFFFFF).toFloat() / 0x7FFFFFFF.toFloat()
}

/**
 * The day arc: where "now" sits between the previous and the next prayer.
 *
 * The only progress indicator in the app. A bar would need a label; an arc does
 * not — it reads as a clock, which is what it is.
 */
@Composable
fun ProgressArc(
    progress: Float,
    color: Color,
    trackColor: Color,
    modifier: Modifier = Modifier
) {
    Canvas(modifier) {
        val stroke = 3.4f * density
        val inset = stroke / 2f
        val diameter = size.minDimension - stroke
        drawArc(
            color = trackColor,
            startAngle = 0f,
            sweepAngle = 360f,
            useCenter = false,
            topLeft = Offset(inset, inset),
            size = Size(diameter, diameter),
            style = Stroke(width = stroke)
        )
        drawArc(
            color = color,
            startAngle = -90f,
            sweepAngle = 360f * progress.coerceIn(0f, 1f),
            useCenter = false,
            topLeft = Offset(inset, inset),
            size = Size(diameter, diameter),
            style = Stroke(width = stroke, cap = StrokeCap.Round)
        )
        // a bead at the head of the arc: this is what makes it feel alive
        val a = Math.toRadians(-90.0 + 360.0 * progress.coerceIn(0f, 1f))
        val cx = size.width / 2f + (diameter / 2f) * cos(a).toFloat()
        val cy = size.height / 2f + (diameter / 2f) * sin(a).toFloat()
        drawCircle(Color.White.copy(alpha = 0.92f), radius = 2.6f * density, center = Offset(cx, cy))
    }
}

/**
 * The compass, for the qibla card.
 *
 * A **true-north** rose, and the label says so. A bearing computed to 0.01° and
 * then shifted by a modelled magnetic declination would claim a precision this
 * app does not have; saying "true north" costs nothing and is honest.
 */
@Composable
fun QiblaCompass(
    bearingDegrees: Double,
    palette: SkyPalette,
    accent: Color,
    modifier: Modifier = Modifier
) {
    Canvas(modifier) {
        val cx = size.width / 2f
        val cy = size.height / 2f
        val r = size.minDimension / 2f - 6f * density

        drawCircle(palette.hairline(), radius = r, center = Offset(cx, cy),
            style = Stroke(width = 1.2f * density))
        drawCircle(palette.hairline().copy(alpha = 0.6f), radius = r * 0.80f,
            center = Offset(cx, cy), style = Stroke(width = 0.8f * density))

        // ticks: long at the cardinals, short between
        for (i in 0 until 36) {
            val a = Math.toRadians(i * 10.0 - 90.0)
            val long = i % 9 == 0
            val mid = i % 3 == 0
            val len = when {
                long -> 14f
                mid -> 8f
                else -> 4f
            } * density
            drawLine(
                color = Color.White.copy(alpha = if (long) 0.65f else 0.26f),
                start = Offset(cx + r * cos(a).toFloat(), cy + r * sin(a).toFloat()),
                end = Offset(cx + (r - len) * cos(a).toFloat(), cy + (r - len) * sin(a).toFloat()),
                strokeWidth = if (long) 1.6f * density else 1f * density
            )
        }

        // the needle
        val q = Math.toRadians(bearingDegrees - 90.0)
        val tip = Offset(
            cx + (r - 10f * density) * cos(q).toFloat(),
            cy + (r - 10f * density) * sin(q).toFloat()
        )
        drawLine(accent, Offset(cx, cy), tip, strokeWidth = 2.6f * density)

        // arrowhead, as two strokes — no glyph resource needed
        val head = 12f * density
        listOf(-18.0, 18.0).forEach { off ->
            val b = Math.toRadians(bearingDegrees - 90.0 + off)
            drawLine(
                accent,
                tip,
                Offset(tip.x - head * cos(b).toFloat(), tip.y - head * sin(b).toFloat()),
                strokeWidth = 2.6f * density
            )
        }
        drawCircle(Color.White.copy(alpha = 0.9f), radius = 3f * density, center = Offset(cx, cy))
    }
}
