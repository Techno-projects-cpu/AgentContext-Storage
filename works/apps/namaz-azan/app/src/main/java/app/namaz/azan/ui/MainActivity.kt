package app.namaz.azan.ui

import android.Manifest
import android.os.Build
import android.content.Intent
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
                // The splash runs once per launch. It is not a delay: it is the
                // moment the app computes today's times, given the sentence that
                // belongs at the start of a thing.
                var screen by remember { mutableStateOf(Screen.SPLASH) }

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
                        Screen.SPLASH -> SplashScreen(
                            sky = state.sky,
                            onFinished = { screen = Screen.HOME }
                        )
                        Screen.HOME -> HomeScreen(
                            state = state,
                            onOpenSettings = { screen = Screen.SETTINGS },
                            onOpenTimetable = { screen = Screen.TIMETABLE },
                            onOpenWebsite = { openWebsite(this) }
                        )
                        Screen.SETTINGS -> SettingsScreen(
                            state = state,
                            viewModel = vm,
                            onBack = { screen = Screen.HOME },
                            onRequestLocationPermission = {
                                requestLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                            },
                            onRequestExactAlarm = { vm.openExactAlarmSettings(this) },
                            onOpenWebsite = { openWebsite(this) }
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

private enum class Screen { SPLASH, HOME, SETTINGS, TIMETABLE }

/**
 * Open a web page, on the one screen in this app that leaves it.
 *
 * This is the only place the app touches the outside world, and it does so by
 * handing the URL to the browser. The app makes no request itself, holds no
 * WebView, and has no network permission — the manifest still has none, and
 * Android will refuse any network call the app attempted. The distinction matters:
 * tapping a link is the user asking for a page, and the browser is theirs.
 *
 * Failure is handled rather than ignored: on a device with no browser installed
 * the chooser throws, and a crash on a credits screen would be a poor trade for a
 * credit.
 */
private fun openWebsite(activity: android.app.Activity) {
    val uri = android.net.Uri.parse(app.namaz.azan.data.Credits.WEBSITE)
    val intent = Intent(Intent.ACTION_VIEW, uri).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    runCatching { activity.startActivity(intent) }
        .onFailure {
            android.widget.Toast.makeText(
                activity,
                "No app available to open ${app.namaz.azan.data.Credits.WEBSITE}",
                android.widget.Toast.LENGTH_LONG
            ).show()
        }
}
