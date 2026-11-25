package app.namaz.azan.ui

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.viewmodel.compose.viewModel
import app.namaz.azan.ui.theme.NamazTheme

class MainActivity : ComponentActivity() {

    private val requestLocation =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) viewModel?.onLocationPermissionGranted()
        }

    private val requestNotifications =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    private var viewModel: MainViewModel? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            NamazTheme {
                val vm: MainViewModel = viewModel()
                viewModel = vm
                val state by vm.state.collectAsState()

                // No navigation library. Three screens, one enum, and no
                // back-stack — which is all this app needs, and a nav graph would
                // be a dependency to keep a stack nothing pushes to twice.
                var screen by remember { mutableStateOf(Screen.HOME) }

                LaunchedEffect(Unit) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        requestNotifications.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                    if (vm.state.value.useDeviceLocation && !vm.hasLocationPermission()) {
                        requestLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                    }
                }

                // The theme follows the sky, so switching screens is a crossfade
                // through the same colour rather than a jump between two palettes.
                Crossfade(
                    targetState = screen,
                    animationSpec = tween(260),
                    label = "screens"
                ) { target ->
                    when (target) {
                        Screen.HOME -> HomeScreen(
                            state = state,
                            onOpenSettings = { screen = Screen.SETTINGS },
                            onOpenTimetable = { screen = Screen.TIMETABLE }
                        )
                        Screen.SETTINGS -> SettingsScreen(
                            state = state,
                            viewModel = vm,
                            onBack = { screen = Screen.HOME },
                            onRequestLocationPermission = {
                                requestLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                            },
                            onRequestExactAlarm = { vm.openExactAlarmSettings(this) }
                        )
                        Screen.TIMETABLE -> TimetableScreen(
                            state = state,
                            onBack = { screen = Screen.HOME }
                        )
                    }
                }
            }
        }
    }
}

private enum class Screen { HOME, SETTINGS, TIMETABLE }
