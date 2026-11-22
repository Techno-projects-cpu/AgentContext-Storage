package app.namaz.azan.ui

import android.app.Application
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings as AndroidSettings
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import app.namaz.azan.core.DayTimes
import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import app.namaz.azan.core.PrayerCalculator
import app.namaz.azan.core.PrayerTime
import app.namaz.azan.data.AzanScheduler
import app.namaz.azan.data.City
import app.namaz.azan.data.LocationHelper
import app.namaz.azan.data.NotificationHelper
import app.namaz.azan.data.Settings
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId

data class UiState(
    val cityName: String = City.DEFAULT,
    val useDeviceLocation: Boolean = false,
    val latitude: Double = 16.3067,
    val longitude: Double = 80.4365,
    val method: Method = Method.KARACHI,
    val madhab: Madhab = Madhab.SHAFI,
    val azanEnabled: Map<Prayer, Boolean> = Prayer.entries.associateWith { true },
    val adjustments: Map<Prayer, Int> = Prayer.entries.associateWith { 0 },
    val azanSound: Boolean = true,
    val day: DayTimes? = null,
    val now: Instant = Instant.now(),
    val next: PrayerTime? = null,
    val nextAzan: PrayerTime? = null,
    val exactAlarmsAllowed: Boolean = true,
    val locationPermission: Boolean = false
) {
    val zone: ZoneId get() = day?.zone ?: ZoneId.systemDefault()

    /** Countdown text for the header card, e.g. "2 h 14 m". */
    val countdown: String
        get() {
            val target = next ?: return "—"
            var seconds = target.instant.epochSecond - now.epochSecond
            if (seconds < 0) seconds = 0
            val h = seconds / 3600
            val m = (seconds % 3600) / 60
            val s = seconds % 60
            return when {
                h > 0 -> "%d h %02d m".format(h, m)
                m > 0 -> "%d m %02d s".format(m, s)
                else -> "%d s".format(s)
            }
        }
}

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val settings = Settings(application)
    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state.asStateFlow()

    init {
        load()
        // One ticker drives both the clock and the countdown.
        viewModelScope.launch {
            while (true) {
                tick()
                delay(1000)
            }
        }
    }

    fun hasLocationPermission(): Boolean = LocationHelper.hasPermission(getApplication())

    fun load() {
        val zone = settings.zone()
        _state.update {
            it.copy(
                cityName = settings.cityName,
                useDeviceLocation = settings.useDeviceLocation,
                latitude = settings.latitude,
                longitude = settings.longitude,
                method = settings.method(),
                madhab = settings.madhab(),
                azanEnabled = Prayer.entries.associateWith { p -> settings.azanEnabled(p) },
                adjustments = settings.adjustments(),
                azanSound = settings.azanSoundEnabled,
                exactAlarmsAllowed = AzanScheduler.canScheduleExact(getApplication()),
                locationPermission = hasLocationPermission()
            )
        }
        recompute(zone = zone)
        reschedule()
    }

    private fun tick() {
        val now = Instant.now()
        val zone = settings.zone()
        val current = _state.value
        // Recompute when the day rolls over, or the first time we run.
        val stale = current.day == null || current.day.date != now.atZone(zone).toLocalDate()
        if (stale) {
            recompute(now, zone)
            reschedule()
        } else {
            _state.update {
                it.copy(
                    now = now,
                    next = it.day?.next(now),
                    nextAzan = AzanScheduler.nextAzan(settings, now)
                )
            }
        }
    }

    private fun recompute(now: Instant = Instant.now(), zone: ZoneId = settings.zone()) {
        val day = PrayerCalculator.forDate(
            now.atZone(zone).toLocalDate(),
            settings.latitude,
            settings.longitude,
            zone,
            settings.method(),
            settings.madhab(),
            settings.adjustments()
        )
        recomputeFrom(day, now)
    }

    private fun recomputeFrom(day: DayTimes, now: Instant = Instant.now()) {
        _state.update {
            it.copy(
                day = day,
                now = now,
                next = day.next(now),
                nextAzan = AzanScheduler.nextAzan(settings, now)
            )
        }
    }

    /** Re-arm the alarm and refresh derived state after any preference change. */
    private fun reschedule() {
        NotificationHelper.ensureChannels(getApplication(), settings.azanSoundEnabled)
        val scheduled = AzanScheduler.scheduleNext(getApplication(), settings)
        _state.update {
            it.copy(
                nextAzan = scheduled,
                exactAlarmsAllowed = AzanScheduler.canScheduleExact(getApplication())
            )
        }
    }

    fun selectCity(city: City) {
        settings.cityName = city.name
        settings.useDeviceLocation = false
        settings.latitude = city.latitude
        settings.longitude = city.longitude
        load()
    }

    fun setUseDeviceLocation(enabled: Boolean) {
        settings.useDeviceLocation = enabled
        if (enabled) {
            LocationHelper.lastKnown(getApplication())?.let { (lat, lon) ->
                settings.latitude = lat
                settings.longitude = lon
            }
        } else {
            val city = settings.city()
            settings.latitude = city.latitude
            settings.longitude = city.longitude
        }
        load()
    }

    fun onLocationPermissionGranted() {
        settings.useDeviceLocation = true
        LocationHelper.lastKnown(getApplication())?.let { (lat, lon) ->
            settings.latitude = lat
            settings.longitude = lon
        }
        load()
    }

    fun selectMethod(method: Method) {
        settings.methodName = method.name
        load()
    }

    fun selectMadhab(madhab: Madhab) {
        settings.madhabName = madhab.name
        load()
    }

    fun toggleAzan(prayer: Prayer, enabled: Boolean) {
        settings.setAzanEnabled(prayer, enabled)
        load()
    }

    fun setAzanSound(enabled: Boolean) {
        settings.azanSoundEnabled = enabled
        load()
    }

    fun setVibrate(enabled: Boolean) {
        settings.vibrateEnabled = enabled
        load()
    }

    fun adjust(prayer: Prayer, minutes: Int) {
        settings.setAdjustMinutes(prayer, minutes)
        load()
    }

    fun openExactAlarmSettings(activity: android.app.Activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val intent = Intent(AndroidSettings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM).apply {
                data = Uri.parse("package:${activity.packageName}")
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            runCatching { activity.startActivity(intent) }
        }
    }

    /** Used by the settings screen to preview the chosen tone. */
    fun currentPrayerForLabel(label: String): Prayer? =
        Prayer.entries.firstOrNull { it.label == label }
}
