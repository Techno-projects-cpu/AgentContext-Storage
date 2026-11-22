package app.namaz.azan.ui

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.LaunchedEffect
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

                LaunchedEffect(Unit) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        requestNotifications.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                    if (vm.state.value.useDeviceLocation && !vm.hasLocationPermission()) {
                        requestLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                    }
                }

                HomeScreen(
                    viewModel = vm,
                    onRequestLocationPermission = {
                        requestLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                    },
                    onRequestExactAlarm = { vm.openExactAlarmSettings(this) }
                )
            }
        }
    }
}
