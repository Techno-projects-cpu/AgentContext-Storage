package app.namaz.azan.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/**
 * Material's colour scheme, used only by the settings screen and dialogs.
 *
 * Deliberately **not** dynamic. Dynamic colour reads the wallpaper and hands back
 * a palette; this app's whole surface is a sky it computes itself, and a
 * wallpaper-derived accent fighting a sunset gradient looks like a bug. The home
 * screen does not consult Material for any colour at all — it takes everything
 * from [app.namaz.azan.ui.theme.SkyPalette] — so this scheme only has to be
 * quiet, dark, and legible underneath that.
 *
 * There is one scheme, not two: the app has no light mode, because the home
 * screen's colour is the time of day, not a user preference.
 */
private val Scheme = darkColorScheme(
    primary = Color(0xFFF5B75C),
    onPrimary = Color(0xFF2A1C00),
    primaryContainer = Color(0xFF4A3312),
    onPrimaryContainer = Color(0xFFFFE0B2),
    secondary = Color(0xFFD6DEEA),
    onSecondary = Color(0xFF11151F),
    background = Color(0xFF0B1020),
    onBackground = Color(0xFFF7F4ED),
    surface = Color(0xFF151B2E),
    onSurface = Color(0xFFF7F4ED),
    surfaceVariant = Color(0xFF1E2438),
    onSurfaceVariant = Color(0xFFC8CDDA),
    outline = Color(0xFF4A5166)
)

@Composable
fun NamazTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Scheme, content = content)
}
