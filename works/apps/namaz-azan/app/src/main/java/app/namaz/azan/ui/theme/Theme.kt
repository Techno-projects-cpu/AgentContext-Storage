package app.namaz.azan.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val Green = Color(0xFF0B6E4F)
private val GreenDark = Color(0xFF06412E)
private val Gold = Color(0xFFD4AF37)
private val Sand = Color(0xFFF6F2E8)

private val Light = lightColorScheme(
    primary = Green,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD8EFE4),
    onPrimaryContainer = Color(0xFF04291D),
    secondary = Gold,
    onSecondary = Color(0xFF241C00),
    secondaryContainer = Color(0xFFFBEFC2),
    onSecondaryContainer = Color(0xFF241C00),
    background = Sand,
    surface = Color.White
)

private val Dark = darkColorScheme(
    primary = Color(0xFF7FD3B0),
    onPrimary = Color(0xFF00382A),
    primaryContainer = GreenDark,
    onPrimaryContainer = Color(0xFFCDEFE0),
    secondary = Gold,
    onSecondary = Color(0xFF241C00),
    secondaryContainer = Color(0xFF4A3D00),
    onSecondaryContainer = Color(0xFFFBEFC2),
    background = Color(0xFF0E1512),
    surface = Color(0xFF141C18)
)

@Composable
fun NamazTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val scheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        darkTheme -> Dark
        else -> Light
    }
    MaterialTheme(colorScheme = scheme, content = content)
}
