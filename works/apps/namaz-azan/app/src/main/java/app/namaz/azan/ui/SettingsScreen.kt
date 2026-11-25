package app.namaz.azan.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.data.City
import app.namaz.azan.ui.theme.SkyInk
import app.namaz.azan.ui.theme.SkyInkDim
import app.namaz.azan.ui.theme.SkyInkGrey
import app.namaz.azan.ui.theme.SunGold
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    state: UiState,
    viewModel: MainViewModel,
    onBack: () -> Unit,
    onRequestLocationPermission: () -> Unit,
    onRequestExactAlarm: () -> Unit,
    onOpenWebsite: () -> Unit = {}
) {
    val sky = state.sky
    Box(Modifier.fillMaxSize().background(sky.ground)) {
        // The same sky, held still and darkened: settings should feel like the
        // same app with the lights turned down, not a different app.
        SkyCanvas(
            palette = sky,
            sunAltitude = state.sunAltitude,
            sunAzimuth = state.sunAzimuth,
            modifier = Modifier.fillMaxSize()
        )
    Scaffold(
        containerColor = androidx.compose.ui.graphics.Color.Transparent,
        topBar = {
            TopAppBar(
                title = { Text("Settings", color = SkyInk) },
                colors = androidx.compose.material3.TopAppBarDefaults.topAppBarColors(
                    containerColor = androidx.compose.ui.graphics.Color.Transparent
                ),
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = SkyInkDim
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            Section("Location") {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("Use my location", fontWeight = FontWeight.Medium, color = SkyInk)
                        Text(
                            "Uses the device's last known position",
                            style = MaterialTheme.typography.bodySmall,
                            color = SkyInkGrey
                        )
                    }
                    Switch(
                        checked = state.useDeviceLocation,
                        onCheckedChange = { on ->
                            if (on && !state.locationPermission) onRequestLocationPermission()
                            else viewModel.setUseDeviceLocation(on)
                        }
                    )
                }
                Spacer(Modifier.height(12.dp))
                Text(
                    "City",
                    style = MaterialTheme.typography.labelLarge,
                    color = SkyInkGrey
                )
                Spacer(Modifier.height(8.dp))
                LazyColumn(Modifier.height(190.dp)) {
                    items(City.ALL.chunked(2)) { pair ->
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .padding(vertical = 3.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            pair.forEach { city ->
                                FilterChip(
                                    selected = city.name == state.cityName && !state.useDeviceLocation,
                                    onClick = { viewModel.selectCity(city) },
                                    label = { Text(city.name, color = SkyInk) },
                                    colors = androidx.compose.material3.FilterChipDefaults
                                        .filterChipColors(
                                            containerColor = Color.White.copy(alpha = 0.08f),
                                            labelColor = SkyInk,
                                            selectedContainerColor = SunGold.copy(alpha = 0.24f),
                                            selectedLabelColor = SkyInk
                                        ),
                                    modifier = Modifier.weight(1f)
                                )
                            }
                            if (pair.size == 1) Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }

            Section("Calculation method") {
                Method.entries.forEach { method ->
                    RadioRow(
                        title = method.label,
                        subtitle = if (method.ishaIntervalMinutes > 0)
                            "Fajr ${method.fajrAngle}° · Isha Maghrib + ${method.ishaIntervalMinutes} min"
                        else "Fajr ${method.fajrAngle}° · Isha ${method.ishaAngle}°",
                        selected = state.method == method,
                        onClick = { viewModel.selectMethod(method) }
                    )
                }
            }

            Section("Asr calculation (madhab)") {
                Madhab.entries.forEach { madhab ->
                    RadioRow(
                        title = madhab.label,
                        subtitle = if (madhab == Madhab.HANAFI)
                            "Asr later — the Hanafi position" else "Asr earlier — Shafi, Maliki, Hanbali",
                        selected = state.madhab == madhab,
                        onClick = { viewModel.selectMadhab(madhab) }
                    )
                }
            }

            Section("Azan") {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("Azan sound", fontWeight = FontWeight.Medium, color = SkyInk)
                        Text(
                            "Plays a chime at each prayer time",
                            style = MaterialTheme.typography.bodySmall,
                            color = SkyInkGrey
                        )
                    }
                    Switch(
                        checked = state.azanSound,
                        onCheckedChange = { viewModel.setAzanSound(it) }
                    )
                }
                Spacer(Modifier.height(10.dp))
                Prayer.entries.filter { it != Prayer.SUNRISE }.forEach { prayer ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(prayer.label, style = MaterialTheme.typography.bodyLarge, color = SkyInk)
                        Switch(
                            checked = state.azanEnabled[prayer] == true,
                            onCheckedChange = { viewModel.toggleAzan(prayer, it) }
                        )
                    }
                }
                if (!state.exactAlarmsAllowed) {
                    Spacer(Modifier.height(8.dp))
                    AssistChip(
                        onClick = onRequestExactAlarm,
                        label = { Text("Allow exact alarms for on-time azan") }
                    )
                }
            }

            Section("Manual adjustment") {
                Text(
                    "Shift a time if it differs from your mosque. Applies to this device only.",
                    style = MaterialTheme.typography.bodySmall,
                    color = SkyInkGrey
                )
                Prayer.entries.forEach { prayer ->
                    val value = state.adjustments[prayer] ?: 0
                    Column(Modifier.padding(vertical = 4.dp)) {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(prayer.label, style = MaterialTheme.typography.bodyLarge, color = SkyInk)
                            Text(
                                "${if (value > 0) "+" else ""}$value min",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                        Slider(
                            value = value.toFloat(),
                            onValueChange = { viewModel.adjust(prayer, it.roundToInt()) },
                            valueRange = -15f..15f,
                            steps = 29
                        )
                    }
                }
            }

            Section("About") {
                Text(
                    "Prayer times are computed on the device with a standard solar algorithm, " +
                        "the same mathematics used by Adhan-compatible libraries. The app has no " +
                        "network permission at all, so it cannot send anything anywhere.",
                    style = MaterialTheme.typography.bodySmall,
                    color = SkyInkGrey
                )
                Spacer(Modifier.height(10.dp))
                Text(
                    "The Hijri date uses the arithmetic Islamic calendar, which can be a day " +
                        "away from a local sighting. Always confirm with your local mosque, " +
                        "especially during Ramadan.",
                    style = MaterialTheme.typography.bodySmall,
                    color = SkyInkGrey
                )
                Spacer(Modifier.height(16.dp))
                Box(Modifier.fillMaxWidth().height(1.dp).background(Color.White.copy(alpha = 0.10f)))
                Spacer(Modifier.height(14.dp))
                SectionRow(
                    title = "Made by ${app.namaz.azan.data.Credits.STUDIO}",
                    subtitle = app.namaz.azan.data.Credits.BYLINE,
                    value = app.namaz.azan.data.Credits.WEBSITE_LABEL
                ) { onOpenWebsite() }
            }
        }
    }
    }
}

@Composable
private fun Section(title: String, content: @Composable () -> Unit) {
    Column {
        Text(
            title.uppercase(),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.Bold
        )
        Spacer(Modifier.height(8.dp))
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f)
            )
        ) {
            Column(Modifier.padding(16.dp)) { content() }
        }
    }
}

/**
 * A label pair with a value on the right and an action, used for the credit row.
 *
 * Rows like this are why settings screens end up feeling unfinished: the value
 * looks tappable and is not, or the whole row is tappable and looks like text.
 * Both the row and the value are clickable here, and the value is in the accent.
 */
@Composable
private fun SectionRow(
    title: String,
    subtitle: String,
    value: String,
    onClick: () -> Unit
) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge, color = SkyInk)
            Spacer(Modifier.height(2.dp))
            Text(subtitle, style = MaterialTheme.typography.labelSmall, color = SkyInkGrey)
        }
        Text(value, style = MaterialTheme.typography.labelMedium, color = SunGold)
        Spacer(Modifier.width(4.dp))
        Text("↗", color = SunGold, fontSize = 13.sp)
    }
}

@Composable
private fun RadioRow(
    title: String,
    subtitle: String,
    selected: Boolean,
    onClick: () -> Unit
) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        androidx.compose.material3.RadioButton(selected = selected, onClick = onClick)
        Spacer(Modifier.width(4.dp))
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge, color = SkyInk)
            Text(
                subtitle,
                style = MaterialTheme.typography.labelSmall,
                color = SkyInkGrey
            )
        }
    }
}
