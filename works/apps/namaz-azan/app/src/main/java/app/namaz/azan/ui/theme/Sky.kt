package app.namaz.azan.ui.theme

import androidx.compose.ui.graphics.Color
import kotlin.math.abs

/**
 * The sky.
 *
 * A phone weather app is beautiful because the whole screen is one thing: the
 * gradient *is* the sky, and cards sit on that light rather than on grey panels.
 * This is the same idea for a prayer app, where it fits even better — the subject
 * of this app literally is the sun.
 *
 * The colour comes from the sun's real altitude at the user's coordinates, so the
 * app is orange at Maghrib in Guntur and daylight blue at the same clock time in
 * London. There is no time-of-day lookup table anywhere.
 *
 * ## The four stops, and why four
 *
 * A sunset is not a two-colour gradient. It is: blue at the top, violet through
 * the middle, a **burning band** a third of the way up from the horizon, and a
 * dark ground beneath it. Interpolating straight from blue to black loses that
 * band and produces mud, which is what the first two drafts of this file did. So
 * the model carries four stops and the band is a real colour in its own right.
 *
 * Warmth only ever lives at the *band* and below. The mid stop stays blue or
 * violet at every hour; that is what stops the sunset from turning grey.
 *
 * ## Why the bottom of the screen is always dark
 *
 * Measured against WCAG, dark ink on a half-lit sunset sky is 1.67:1 — nowhere
 * near the 4.5:1 body text needs, and no card translucency fixes it. So the sky
 * keeps its colour up top and deepens toward the ground, the way a real horizon
 * does. Content always sits on the deep part; there is exactly one ink, a warm
 * off-white, and the worst contrast anywhere in the day measures **6.9:1**.
 *
 * Angles are degrees above the horizon.
 */

/** A four-stop vertical sky, top of screen to bottom. */
data class SkyPalette(
    val zenith: Color,
    /** The sky's own colour, about 38% down. */
    val mid: Color,
    /** The warm band, about 66% down. This is the sunset. */
    val band: Color,
    /** The deep ground content sits on, at the bottom. */
    val ground: Color,
    /** 0 at noon, 1 at astronomical night. */
    val night: Float
)

private fun lerp(a: Float, b: Float, t: Float) = a + (b - a) * t

private fun mix(a: Color, b: Color, t: Float): Color {
    val u = t.coerceIn(0f, 1f)
    return Color(
        red = lerp(a.red, b.red, u),
        green = lerp(a.green, b.green, u),
        blue = lerp(a.blue, b.blue, u),
        alpha = 1f
    )
}

/** Near-black with a blue cast. Grounds are mixed toward this, not toward pure black. */
private val DEEP = Color(0xFF07090F)

/**
 * The ground for a given band colour: the band's own hue, taken most of the way
 * down. Derived per palette, so a sunset's ground is warm-dark and noon's is
 * blue-dark — which is what keeps the app from looking identical all day.
 */
private fun groundOf(band: Color): Color = mix(band, DEEP, 0.66f)

// --- the named skies ---------------------------------------------------------
/** Midday: deep blue overhead, pale at the band, blue-grey ground. */
private val DAY = SkyPalette(
    zenith = Color(0xFF1B5FA8),
    mid = Color(0xFF3E8FD0),
    band = Color(0xFF8FC4E4),
    ground = groundOf(Color(0xFF8FC4E4)),
    night = 0.04f
)

/** The hour after sunrise: cool above, warm haze below. */
private val MORNING = SkyPalette(
    zenith = Color(0xFF2A6FB5),
    mid = Color(0xFF5A8FC4),
    band = Color(0xFFE8B77E),
    ground = groundOf(Color(0xFFE8B77E)),
    night = 0.12f
)

/** Golden hour. The app's second-best frame. */
private val GOLDEN = SkyPalette(
    zenith = Color(0xFF31558C),
    mid = Color(0xFF4A73A8),
    band = Color(0xFFF0A253),
    ground = groundOf(Color(0xFFF0A253)),
    night = 0.24f
)

/** The moment of sunset. The app's best frame. */
private val SUNSET = SkyPalette(
    zenith = Color(0xFF2B3560),
    mid = Color(0xFF54507A),
    band = Color(0xFFF2803C),
    ground = groundOf(Color(0xFFF2803C)),
    night = 0.40f
)

/** Civil twilight: the last orange is a band, everything above is blue-black. */
private val CIVIL = SkyPalette(
    zenith = Color(0xFF18214A),
    mid = Color(0xFF2E3054),
    band = Color(0xFFB85C46),
    ground = groundOf(Color(0xFFB85C46)),
    night = 0.66f
)

/** Nautical twilight: the horizon still glows faintly. */
private val NAUTICAL = SkyPalette(
    zenith = Color(0xFF0A1026),
    mid = Color(0xFF121733),
    band = Color(0xFF4A3A60),
    ground = groundOf(Color(0xFF4A3A60)),
    night = 0.86f
)

/** Astronomical night. */
private val NIGHT = SkyPalette(
    zenith = Color(0xFF05081A),
    mid = Color(0xFF0A1024),
    band = Color(0xFF1E2340),
    ground = groundOf(Color(0xFF1E2340)),
    night = 1.00f
)

/**
 * The sky for a given solar altitude. Bands are interpolated, never stepped, so a
 * clock ticking through sunset is a continuous wash rather than a slideshow.
 */
fun skyForSunAltitude(altitudeDegrees: Double): SkyPalette {
    val a = altitudeDegrees
    return when {
        a >= 30.0 -> DAY
        a >= 10.0 -> mixPalette(MORNING, DAY, ((a - 10.0) / 20.0).toFloat())
        a >= 4.0 -> mixPalette(GOLDEN, MORNING, ((a - 4.0) / 6.0).toFloat())
        a >= -0.8 -> mixPalette(SUNSET, GOLDEN, ((a + 0.8) / 4.8).toFloat())
        a >= -6.0 -> mixPalette(CIVIL, SUNSET, ((a + 6.0) / 5.2).toFloat())
        a >= -12.0 -> mixPalette(NAUTICAL, CIVIL, ((a + 12.0) / 6.0).toFloat())
        a >= -18.0 -> mixPalette(NIGHT, NAUTICAL, ((a + 18.0) / 6.0).toFloat())
        else -> NIGHT
    }
}

fun mixPalette(a: SkyPalette, b: SkyPalette, t: Float): SkyPalette {
    val u = t.coerceIn(0f, 1f)
    return SkyPalette(
        zenith = mix(a.zenith, b.zenith, u),
        mid = mix(a.mid, b.mid, u),
        band = mix(a.band, b.band, u),
        ground = mix(a.ground, b.ground, u),
        night = lerp(a.night, b.night, u)
    )
}

// --- ink ---------------------------------------------------------------------

/**
 * The one ink: a warm off-white. Pure white reads cold against a blue sky; warm
 * white carries the sunset's colour up into the type.
 */
val SkyInk = Color(0xFFF7F4ED)

/** Secondary text. */
val SkyInkDim = Color(0xFFF7F4ED).copy(alpha = 0.74f)

/** Labels and units. Still clears 4.5:1 against the deepest ground. */
val SkyInkFaint = Color(0xFFF7F4ED).copy(alpha = 0.56f)

/**
 * Secondary ink as an opaque colour rather than an alpha.
 *
 * The settings screen uses this instead of [SkyInkFaint] because Material's text
 * composables composite their own alpha on top; an already-translucent colour
 * would come out twice as faint and drop below 4.5:1.
 */
val SkyInkGrey = Color(0xFFBFBEBB)

// --- glass -------------------------------------------------------------------

/**
 * Glass for a card: the *ground* colour lifted slightly with white, laid at half
 * opacity over that same ground.
 *
 * It is derived from the ground rather than from the band on purpose. The first
 * version of this used the warm band colour, which put a lit panel in the middle
 * of the frame and dropped the ink to 3.7:1 right at sunset. Building the card
 * from the ground keeps it in the shadow where text lives, and the whole day
 * clears AA with room: worst case **6.9:1**, at midday.
 */
fun SkyPalette.glass(): Color = mix(ground, Color.White, 0.14f).copy(alpha = 0.50f)

/** The hero card is a touch more present, so the countdown sits on it cleanly. */
fun SkyPalette.glassHero(): Color = mix(ground, Color.White, 0.18f).copy(alpha = 0.62f)

/** Hairline that reads on any sky. */
fun SkyPalette.hairline(): Color = Color.White.copy(alpha = 0.20f)

/** A stronger hairline for the hero card. */
fun SkyPalette.hairlineStrong(): Color = Color.White.copy(alpha = 0.28f)

// --- accents -----------------------------------------------------------------

/** The sun. Warm, never white, so it never disappears into a bright sky. */
val SunGold = Color(0xFFF5B75C)
val SunGoldDeep = Color(0xFFE08E2E)

/** The moon and stars: cool, so night has a colour of its own. */
val MoonSilver = Color(0xFFD6DEEA)

/**
 * Accent for "this is happening now" — the live prayer, the arc bead. Slides from
 * the sun's gold to the moon's silver as night comes in, so the accent belongs to
 * the hour it marks.
 */
fun SkyPalette.accent(): Color = mix(SunGold, MoonSilver, night.coerceIn(0f, 1f))

/** Ramp for the day-arc, from pre-dawn through noon to late night. */
fun SkyPalette.accentDeep(): Color = mix(SunGoldDeep, Color(0xFF8FA6C4), night.coerceIn(0f, 1f))

// --- placing the light -------------------------------------------------------

/**
 * How hard the sun's bloom bleeds in, 0..1. Peaks near the horizon, where the
 * atmosphere scatters most, and is almost nothing at night.
 */
fun sunGlowStrength(altitudeDegrees: Double): Float {
    val a = altitudeDegrees
    return when {
        a >= 20.0 -> 0.10f
        a >= 0.0 -> 0.14f + 0.52f * ((20.0 - a) / 20.0).toFloat()
        a >= -8.0 -> (0.60f * (1f + a.toFloat() / 8f) + 0.14f).coerceAtLeast(0.10f)
        else -> 0.08f
    }
}

/**
 * Vertical centre of the **disc**, 0 (bottom of frame) .. 1 (top).
 *
 * The disc is placed for composition rather than for physics: it lives in the top
 * quarter, above every card, so it reads as a sun in the sky rather than as a
 * smudge behind glass. At dusk it drops toward the top of the content but never
 * into it.
 */
fun sunDiscCentreY(altitudeDegrees: Double): Float {
    // High sun rides up into the header band, where there is no card to cover it
    // and where it reads as a light source in the corner of the sky.
    val t = ((altitudeDegrees + 10.0) / 45.0).coerceIn(0.0, 1.0).toFloat()
    return 0.135f - 0.055f * t
}

/**
 * Vertical centre of the **bloom**, 0 (bottom) .. 1 (top).
 *
 * Separate from the disc, and fixed near the warm band at 0.62, because that is
 * where the atmosphere actually scatters the light — the glow belongs on the
 * horizon even when the sun has sunk below it.
 */
fun sunGlowCentreY(@Suppress("UNUSED_PARAMETER") altitudeDegrees: Double): Float = 0.60f

/** Horizontal radius of the bloom, as a fraction of screen width. */
fun sunGlowRadiusFraction(altitudeDegrees: Double): Float {
    val t = ((10.0 - altitudeDegrees) / 18.0).coerceIn(0.0, 1.0).toFloat()
    return 0.70f + 0.16f * t
}

/** Sun disc radius in dp: small overhead, large and soft at dusk. */
fun sunDiscRadius(altitudeDegrees: Double): Float {
    val t = ((altitudeDegrees + 8.0) / 40.0).coerceIn(0.0, 1.0).toFloat()
    return 26f - 9f * t
}

/** Colour of the disc: white-hot overhead, deep orange at the horizon. */
fun sunDiscColor(altitudeDegrees: Double): Color {
    val t = ((altitudeDegrees + 2.0) / 32.0).coerceIn(0.0, 1.0).toFloat()
    return mix(Color(0xFFFFC46B), Color(0xFFFFF6E0), t)
}

/** True when the moon, not the sun, should be drawn. */
fun isNight(sunAltitude: Double): Boolean = sunAltitude < -0.8

/** Magnitude of a colour difference — used by tests and by debugging. */
fun colorDistance(a: Color, b: Color): Float {
    val dr = abs(a.red - b.red)
    val dg = abs(a.green - b.green)
    val db = abs(a.blue - b.blue)
    return (dr + dg + db) / 3f
}
