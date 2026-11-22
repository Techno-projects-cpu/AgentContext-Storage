package app.namaz.azan.data

import android.content.Context
import android.content.SharedPreferences
import app.namaz.azan.core.Madhab
import app.namaz.azan.core.Method
import app.namaz.azan.core.Prayer
import java.time.ZoneId

/** A place the user can pick from. Defaults to Guntur. */
data class City(val name: String, val latitude: Double, val longitude: Double, val zone: ZoneId) {
    companion object {
        private val IST = ZoneId.of("Asia/Kolkata")
        val ALL = listOf(
            City("Guntur", 16.3067, 80.4365, IST),
            City("Vijayawada", 16.5062, 80.6480, IST),
            City("Hyderabad", 17.3850, 78.4867, IST),
            City("Visakhapatnam", 17.6868, 83.2185, IST),
            City("Tirupati", 13.6288, 79.4192, IST),
            City("Warangal", 17.9689, 79.5941, IST),
            City("Rajahmundry", 17.0005, 81.8040, IST),
            City("Nellore", 14.4426, 79.9865, IST),
            City("Bengaluru", 12.9716, 77.5946, IST),
            City("Chennai", 13.0827, 80.2707, IST),
            City("Mumbai", 19.0760, 72.8777, IST),
            City("Delhi", 28.6139, 77.2090, IST),
            City("Kolkata", 22.5726, 88.3639, IST),
            City("Makkah", 21.4225, 39.8262, ZoneId.of("Asia/Riyadh")),
            City("Madinah", 24.4672, 39.6111, ZoneId.of("Asia/Riyadh")),
            City("Dubai", 25.2048, 55.2708, ZoneId.of("Asia/Dubai"))
        )
        val DEFAULT = "Guntur"
    }
}

/**
 * All user preferences, backed by SharedPreferences.
 *
 * Deliberately dependency-free: the app needs no database, and fewer libraries
 * means a smaller APK and no instrumentation to fail in CI.
 */
class Settings(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("namaz_settings", Context.MODE_PRIVATE)

    var cityName: String
        get() = prefs.getString(KEY_CITY, City.DEFAULT) ?: City.DEFAULT
        set(v) = prefs.edit().putString(KEY_CITY, v).apply()

    /** When true, coordinates come from the device instead of the chosen city. */
    var useDeviceLocation: Boolean
        get() = prefs.getBoolean(KEY_USE_GPS, false)
        set(v) = prefs.edit().putBoolean(KEY_USE_GPS, v).apply()

    var latitude: Double
        get() = prefs.getFloat(KEY_LAT, 0f).toDouble().takeIf { it != 0.0 } ?: city().latitude
        set(v) = prefs.edit().putFloat(KEY_LAT, v.toFloat()).apply()

    var longitude: Double
        get() = prefs.getFloat(KEY_LON, 0f).toDouble().takeIf { it != 0.0 } ?: city().longitude
        set(v) = prefs.edit().putFloat(KEY_LON, v.toFloat()).apply()

    var methodName: String
        get() = prefs.getString(KEY_METHOD, Method.KARACHI.name) ?: Method.KARACHI.name
        set(v) = prefs.edit().putString(KEY_METHOD, v).apply()

    var madhabName: String
        get() = prefs.getString(KEY_MADHAB, Madhab.SHAFI.name) ?: Madhab.SHAFI.name
        set(v) = prefs.edit().putString(KEY_MADHAB, v).apply()

    var azanSoundEnabled: Boolean
        get() = prefs.getBoolean(KEY_AZAN_SOUND, true)
        set(v) = prefs.edit().putBoolean(KEY_AZAN_SOUND, v).apply()

    var vibrateEnabled: Boolean
        get() = prefs.getBoolean(KEY_VIBRATE, true)
        set(v) = prefs.edit().putBoolean(KEY_VIBRATE, v).apply()

    fun azanEnabled(prayer: Prayer): Boolean =
        prefs.getBoolean("azan_${prayer.name}", true)

    fun setAzanEnabled(prayer: Prayer, enabled: Boolean) =
        prefs.edit().putBoolean("azan_${prayer.name}", enabled).apply()

    fun adjustMinutes(prayer: Prayer): Int = prefs.getInt("adj_${prayer.name}", 0)

    fun setAdjustMinutes(prayer: Prayer, minutes: Int) =
        prefs.edit().putInt("adj_${prayer.name}", minutes).apply()

    fun city(): City =
        City.ALL.firstOrNull { it.name == cityName } ?: City.ALL.first()

    fun method(): Method =
        Method.entries.firstOrNull { it.name == methodName } ?: Method.KARACHI

    fun madhab(): Madhab =
        Madhab.entries.firstOrNull { it.name == madhabName } ?: Madhab.SHAFI

    fun adjustments(): Map<Prayer, Int> = Prayer.entries.associateWith { adjustMinutes(it) }

    fun zone(): ZoneId = if (useDeviceLocation) ZoneId.systemDefault() else city().zone

    private companion object {
        const val KEY_CITY = "city"
        const val KEY_USE_GPS = "use_gps"
        const val KEY_LAT = "lat"
        const val KEY_LON = "lon"
        const val KEY_METHOD = "method"
        const val KEY_MADHAB = "madhab"
        const val KEY_AZAN_SOUND = "azan_sound"
        const val KEY_VIBRATE = "vibrate"
    }
}
