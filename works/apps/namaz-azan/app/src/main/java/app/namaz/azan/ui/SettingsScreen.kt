package app.namaz.azan.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.data.City
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    state: UiState,
    viewModel: MainViewModel,
    onBack: () -> Unit,
    onRequestLocationPermission: () -> Unit,
    onRequestExactAlarm: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
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
                        Text("Use my location", fontWeight = FontWeight.Medium)
                        Text(
                            "Uses the device's last known position",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
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
                    color = MaterialTheme.colorScheme.onSurfaceVariant
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
                                    label = { Text(city.name) },
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
                        Text("Azan sound", fontWeight = FontWeight.Medium)
                        Text(
                            "Plays a chime at each prayer time",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
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
                        Text(prayer.label, style = MaterialTheme.typography.bodyLarge)
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
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Prayer.entries.forEach { prayer ->
                    val value = state.adjustments[prayer] ?: 0
                    Column(Modifier.padding(vertical = 4.dp)) {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(prayer.label, style = MaterialTheme.typography.bodyLarge)
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
                        "the same mathematics used by Adhan-compatible libraries. No network " +
                        "connection is needed and no location data leaves the phone.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    "Always confirm with your local mosque, especially during Ramadan.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
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
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(
                subtitle,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
