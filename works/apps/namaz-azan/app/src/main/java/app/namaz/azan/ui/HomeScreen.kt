package app.namaz.azan.ui

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.SizeTransform
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateIntAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.namaz.azan.core.PrayerTime
import app.namaz.azan.ui.theme.SkyInk
import app.namaz.azan.ui.theme.SkyInkDim
import app.namaz.azan.ui.theme.SkyInkFaint
import app.namaz.azan.ui.theme.SkyPalette
import app.namaz.azan.ui.theme.SunGold
import app.namaz.azan.ui.theme.accent
import app.namaz.azan.ui.theme.glass
import app.namaz.azan.ui.theme.glassHero
import app.namaz.azan.ui.theme.hairline
import app.namaz.azan.ui.theme.hairlineStrong

/**
 * The home screen.
 *
 * One full-bleed sky, and five bands of information on it, in the order a person
 * actually asks for them:
 *
 *   1. Where am I, and what day is it — place, Hijri date, next prayer.
 *   2. How long until it — one enormous number, and one arc underneath it.
 *   3. What the day looks like — a horizontal strip of the six times, with the
 *      ones already past dimmed. This is the weather app's hourly strip, and it
 *      does the same job: it answers "what happens next" in a glance.
 *   4. The night — Imsak, midnight, last third, and how long the night is.
 *   5. Qibla and a way into settings.
 *
 * Every colour comes from [SkyPalette], which comes from the sun's real altitude,
 * so this screen is orange at Maghrib and blue at noon without a single time
 * check anywhere in it.
 */
@Composable
fun HomeScreen(
    state: UiState,
    onOpenSettings: () -> Unit,
    onOpenTimetable: () -> Unit = {},
    onOpenWebsite: () -> Unit = {}
) {
    val sky = state.sky
    val accent by animateColorAsState(sky.accent(), tween(1200), label = "accent")

    Box(Modifier.fillMaxSize()) {
        // 1. the sky itself
        SkyCanvas(
            palette = sky,
            sunAltitude = state.sunAltitude,
            sunAzimuth = state.sunAzimuth,
            modifier = Modifier.fillMaxSize()
        )

        // 2. everything on top of it
        Column(
            Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
        ) {
            Spacer(Modifier.height(6.dp))
            Header(state, onOpenSettings, onOpenTimetable)

            Spacer(Modifier.height(26.dp))
            NextPrayerHero(state, sky, accent)

            Spacer(Modifier.height(22.dp))
            DayStrip(state, sky, accent)

            Spacer(Modifier.height(16.dp))
            NightPanel(state, sky)

            Spacer(Modifier.height(16.dp))
            WeekPanel(state, sky, accent)

            Spacer(Modifier.height(16.dp))
            SeasonPanel(state, sky)

            Spacer(Modifier.height(16.dp))
            QiblaPanel(state, sky, accent)

            Spacer(Modifier.height(16.dp))
            MadeByCard(sky, onOpenWebsite)

            Spacer(Modifier.height(28.dp))
            Footer(state)
            // Room for the navigation bar, so the footer never sits under it.
            Spacer(Modifier.height(48.dp))
        }
    }
}

/** Line 1: the place, quietly. Line 2: the Hijri date. Line 3: the next prayer. */
@Composable
private fun Header(
    state: UiState,
    onOpenSettings: () -> Unit,
    onOpenTimetable: () -> Unit
) {
    Row(
        Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                text = state.cityName,
                color = SkyInk,
                fontSize = 17.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.2.sp
            )
            val hijri = state.day?.hijri
            if (hijri != null) {
                Spacer(Modifier.height(3.dp))
                Text(
                    text = "${hijri.day} ${hijri.monthName} ${hijri.year} AH",
                    color = SkyInkDim,
                    fontSize = 13.sp,
                    letterSpacing = 0.3.sp
                )
            }
            Spacer(Modifier.height(2.dp))
            Text(
                text = gregorianLine(state),
                color = SkyInkFaint,
                fontSize = 12.sp,
                letterSpacing = 0.4.sp
            )
        }
        // The month, reachable in one tap from the top of the screen, the way a
        // weather app puts its forecast list one tap from the current conditions.
        Text(
            text = "Month",
            color = SkyInkDim,
            fontSize = 13.sp,
            modifier = Modifier
                .clip(RoundedCornerShape(50))
                .background(Color.White.copy(alpha = 0.10f))
                .clickable(onClick = onOpenTimetable)
                .padding(horizontal = 14.dp, vertical = 7.dp)
        )
        Spacer(Modifier.width(4.dp))
        IconButton(onClick = onOpenSettings) {
            Icon(
                imageVector = Icons.Filled.Settings,
                contentDescription = "Settings",
                tint = SkyInkDim,
                modifier = Modifier.size(22.dp)
            )
        }
    }
}

private fun gregorianLine(state: UiState): String {
    val date = state.day?.date ?: return ""
    val dow = date.dayOfWeek.name.lowercase().replaceFirstChar { it.uppercase() }
    val month = date.month.name.lowercase().replaceFirstChar { it.uppercase() }
    return "$dow, ${date.dayOfMonth} $month"
}

/**
 * The hero: the next prayer, the countdown, and the arc between the two prayers
 * that bracket now.
 *
 * The numeral is the largest thing on the screen by a factor of three. That is
 * the entire typographic idea of a weather app — one number, big enough to read
 * from arm's length — and the same is true here: the countdown is the one figure
 * somebody opens the app to see.
 */
@Composable
private fun NextPrayerHero(state: UiState, sky: SkyPalette, accent: Color) {
    val next = state.nextAcrossDays
    val (big, small) = state.countdownParts
    val progress by animateFloatAsState(
        targetValue = state.progress,
        animationSpec = tween(900, easing = FastOutSlowInEasing),
        label = "progress"
    )
    val percent by animateIntAsState(
        targetValue = (state.progress * 100).toInt(),
        animationSpec = tween(900, easing = FastOutSlowInEasing),
        label = "percent"
    )

    GlassCard(sky, hero = true) {
        Row(
            Modifier.fillMaxWidth().padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(Modifier.weight(1f)) {
                // The label cross-fades rather than cuts when the prayer changes,
                // so the card never flashes in the middle of the evening.
                AnimatedContent(
                    targetState = heroLabel(state, next),
                    transitionSpec = {
                        (fadeIn(tween(320)) togetherWith fadeOut(tween(180)))
                            .using(SizeTransform(clip = false))
                    },
                    label = "heroLabel"
                ) { label ->
                    Text(
                        text = label,
                        color = SkyInkDim,
                        fontSize = 14.sp,
                        letterSpacing = 0.8.sp
                    )
                }
                Spacer(Modifier.height(4.dp))

                // The numerals: a mechanical counter, not a text swap.
                //
                // Each tick moves the digit that changed. Old digit exits upward
                // while the new one rises into place — the movement a physical
                // odometer makes, and the reason a countdown feels alive rather
                // than re-rendered.
                Row(verticalAlignment = Alignment.Bottom) {
                    CountdownNumber(
                        value = big,
                        fontSize = if (big.length > 2) 56.sp else 68.sp,
                        color = SkyInk
                    )
                    if (small.isNotEmpty()) {
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = small,
                            color = SkyInkDim,
                            fontSize = 17.sp,
                            modifier = Modifier.padding(bottom = 14.dp)
                        )
                    }
                }

                if (next != null) {
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = buildString {
                            if (state.nextIsTomorrow) append("tomorrow at ")
                            else append("at ")
                            append(format(next))
                        },
                        color = SkyInkDim,
                        fontSize = 13.sp
                    )
                }
            }

            // the arc: how far through the current window we are
            Box(
                Modifier.size(74.dp),
                contentAlignment = Alignment.Center
            ) {
                ProgressArc(
                    progress = progress,
                    color = accent,
                    trackColor = Color.White.copy(alpha = 0.16f),
                    modifier = Modifier.fillMaxSize()
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = percent.toString(),
                        color = SkyInk,
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "%",
                        color = SkyInkFaint,
                        fontSize = 10.sp
                    )
                }
            }
        }
    }
}

/** "Maghrib in", or "Fajr tomorrow" when the next prayer is after midnight. */
private fun heroLabel(state: UiState, next: PrayerTime?): String = when {
    next == null -> "Next prayer"
    state.nextIsTomorrow -> "${next.prayer.label} tomorrow"
    else -> "${next.prayer.label} in"
}

/**
 * The countdown numeral, sliding like an odometer.
 *
 * The number is treated as a unit rather than animated per-character: a per-digit
 * animation needs the two strings to be the same length, and a countdown drops
 * from 100 to 99 and from 10 to 9. Sliding the whole figure keeps every value
 * correct and still gives the vertical movement that makes it feel mechanical.
 */
@Composable
private fun CountdownNumber(
    value: String,
    fontSize: androidx.compose.ui.unit.TextUnit,
    color: Color
) {
    AnimatedContent(
        targetState = value,
        transitionSpec = {
            // Up and out on the old, up and in on the new: one direction, always.
            (slideInVertically(tween(280)) { h -> h / 2 } + fadeIn(tween(280)))
                .togetherWith(slideOutVertically(tween(220)) { h -> -h / 2 } + fadeOut(tween(200)))
                .using(SizeTransform(clip = false))
        },
        label = "countdown"
    ) { target ->
        Text(
            text = target,
            color = color,
            fontSize = fontSize,
            fontWeight = FontWeight.Light,
            letterSpacing = (-2).sp,
            maxLines = 1
        )
    }
}

/**
 * The horizontal strip of the day's times.
 *
 * Six columns, past ones dimmed, the next one marked with the accent. No
 * scrolling needed at any normal width, which is the point — a weather app's
 * hourly strip is glanceable because nothing is hidden behind a gesture.
 */
@Composable
private fun DayStrip(state: UiState, sky: SkyPalette, accent: Color) {
    val times = state.day?.times ?: return
    val nextPrayer = state.next?.prayer

    GlassCard(sky) {
        Row(
            Modifier.fillMaxWidth().padding(vertical = 16.dp, horizontal = 8.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            times.forEach { time ->
                val isNext = time.prayer == nextPrayer
                val isPast = !time.instant.isAfter(state.now)
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.width(52.dp)
                ) {
                    Text(
                        text = time.prayer.label.take(3),
                        color = if (isNext) SkyInk else SkyInkFaint,
                        fontSize = 11.sp,
                        letterSpacing = 0.5.sp,
                        fontWeight = if (isNext) FontWeight.SemiBold else FontWeight.Normal
                    )
                    Spacer(Modifier.height(7.dp))
                    // a dot instead of an icon: the app has no weather glyphs and
                    // inventing one per prayer would be decoration, not information
                    Box(contentAlignment = Alignment.Center) {
                        if (isNext) PulseHalo(accent)
                        Box(
                            Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(
                                    when {
                                        isNext -> accent
                                        isPast -> Color.White.copy(alpha = 0.12f)
                                        else -> Color.White.copy(alpha = 0.32f)
                                    }
                                )
                        )
                    }
                    Spacer(Modifier.height(7.dp))
                    Text(
                        text = format(time),
                        color = when {
                            isNext -> SkyInk
                            isPast -> SkyInkFaint.copy(alpha = 0.55f)
                            else -> SkyInk
                        },
                        fontSize = 13.sp,
                        fontWeight = if (isNext) FontWeight.SemiBold else FontWeight.Normal,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
    }
}

/**
 * A slow halo around the next prayer's dot.
 *
 * The strip already marks the next prayer with colour and weight, but at arm's
 * length on a bright sky a 6 dp dot is easy to miss. The halo expands and fades on
 * a 2.6 s loop — slow enough not to nag, present enough to find. It stops entirely
 * when the system asks for reduced motion, because an animation that cannot be
 * switched off is a bug on a screen somebody has to sit in front of.
 */
@Composable
private fun PulseHalo(color: Color) {
    val motion = LocalMotionDuration()
    if (motion == 0) return
    val transition = rememberInfiniteTransition(label = "halo")
    val t by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2600, easing = LinearOutSlowInEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "haloProgress"
    )
    Box(
        Modifier
            .size((6 + 14 * t).dp)
            .clip(CircleShape)
            .background(color.copy(alpha = (1f - t) * 0.34f))
    )
}

/**
 * Respect the platform's animation setting.
 *
 * Android exposes the animator duration scale; at 0 the user has turned animation
 * off, usually for a reason (motion sensitivity, an old phone, a battery at 2%).
 * The app keeps its cross-fades — those are information, not decoration — but the
 * idle loops stop.
 */
@Composable
private fun LocalMotionDuration(): Int {
    val context = androidx.compose.ui.platform.LocalContext.current
    return remember(context) {
        android.provider.Settings.Global.getFloat(
            context.contentResolver,
            android.provider.Settings.Global.ANIMATOR_DURATION_SCALE,
            1f
        ).let { if (it == 0f) 0 else 1 }
    }
}

/**
 * The night: the three times that divide it, which no other screen in the app
 * shows, and the reason a Muslim opens a prayer app before bed or before dawn.
 */
@Composable
private fun NightPanel(state: UiState, sky: SkyPalette) {
    val day = state.day ?: return
    val nightLen = day.nightMinutes

    GlassCard(sky) {
        Column(Modifier.fillMaxWidth().padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "THE NIGHT",
                    color = SkyInkFaint,
                    fontSize = 11.sp,
                    letterSpacing = 1.6.sp,
                    modifier = Modifier.weight(1f)
                )
                Text(
                    text = formatDuration(nightLen),
                    color = SkyInkDim,
                    fontSize = 12.sp
                )
            }
            Spacer(Modifier.height(14.dp))
            Row(Modifier.fillMaxWidth()) {
                NightCell("Imsak", day.imsak?.let { formatClock(it) } ?: "—",
                    "10 min before Fajr", Modifier.weight(1f))
                NightCell("Midnight", day.midnight?.let { formatClock(it) } ?: "—",
                    "half the night", Modifier.weight(1f))
                NightCell("Last third", day.lastThird?.let { formatClock(it) } ?: "—",
                    "tahajjud begins", Modifier.weight(1f))
            }
            if (day.isRamadan) {
                Spacer(Modifier.height(14.dp))
                RamadanNote(day)
            }
        }
    }
}

@Composable
private fun NightCell(label: String, value: String, note: String, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(label, color = SkyInkFaint, fontSize = 10.sp, letterSpacing = 0.6.sp)
        Spacer(Modifier.height(5.dp))
        Text(value, color = SkyInk, fontSize = 16.sp, fontWeight = FontWeight.Medium)
        Spacer(Modifier.height(3.dp))
        Text(note, color = SkyInkFaint.copy(alpha = 0.8f), fontSize = 9.sp)
    }
}

/**
 * Ramadan is the one time of year the app should say something it otherwise would
 * not. It also explains why Isha moved, if the chosen method extends it.
 */
@Composable
private fun RamadanNote(day: app.namaz.azan.core.DayTimes) {
    val card = day.hijri ?: return
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Color.White.copy(alpha = 0.07f))
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier.size(5.dp).clip(CircleShape).background(SkyInk)
        )
        Spacer(Modifier.width(9.dp))
        Text(
            text = "Ramadan ${card.day} AH — Isha held to the Ramadan interval",
            color = SkyInkDim,
            fontSize = 11.sp
        )
    }
}

/**
 * How the year is moving.
 *
 * A weather app can tell you it will rain; this app can tell you the daylight is
 * shrinking by a minute and a half a week and that Ramadan is three months out.
 * That is the same "and here is the shape of the time ahead" service, using the
 * thing this app actually knows — the sun.
 *
 * Everything here is derived from dates already computed for the week, except the
 * Ramadan countdown, which comes from [app.namaz.azan.core.HijriCalendar].
 */
@Composable
private fun SeasonPanel(state: UiState, sky: SkyPalette) {
    val week = state.week
    if (week.size < 7) return

    val today = week.first()
    val weekOut = week.last()
    val ratePerWeek = weekOut.daylightMinutes - today.daylightMinutes
    val nightNow = today.nightMinutes

    GlassCard(sky) {
        Column(Modifier.fillMaxWidth().padding(18.dp)) {
            Text(
                text = "THE YEAR",
                color = SkyInkFaint,
                fontSize = 11.sp,
                letterSpacing = 1.6.sp
            )
            Spacer(Modifier.height(12.dp))
            Row(Modifier.fillMaxWidth()) {
                SeasonStat(
                    value = formatMinutesOfDaylight(today.daylightMinutes),
                    label = "of daylight today",
                    modifier = Modifier.weight(1f)
                )
                SeasonStat(
                    value = when {
                        ratePerWeek == 0 -> "no change"
                        ratePerWeek > 0 -> "+${ratePerWeek} min"
                        else -> "$ratePerWeek min"
                    },
                    label = "over the next 7 days",
                    modifier = Modifier.weight(1f)
                )
            }
            Spacer(Modifier.height(14.dp))

            val ramadan = state.daysToRamadan
            val line = when {
                ramadan == null -> null
                ramadan == 0 -> "It is Ramadan. Isha follows the Ramadan rule for this method."
                ramadan == 1 -> "Ramadan begins tomorrow."
                else -> "Ramadan begins in $ramadan days."
            }
            if (line != null) {
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(Color.White.copy(alpha = 0.08f))
                )
                Spacer(Modifier.height(12.dp))
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = line,
                        color = SkyInkDim,
                        fontSize = 12.sp,
                        modifier = Modifier.weight(1f)
                    )
                    Text(
                        text = "night ${formatMinutesOfDaylight(nightNow)}",
                        color = SkyInkFaint,
                        fontSize = 11.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun SeasonStat(value: String, label: String, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(value, color = SkyInk, fontSize = 26.sp, fontWeight = FontWeight.Light)
        Spacer(Modifier.height(3.dp))
        Text(label, color = SkyInkFaint, fontSize = 11.sp)
    }
}

private fun formatMinutesOfDaylight(minutes: Int): String =
    "${minutes / 60}h ${(minutes % 60).toString().padStart(2, '0')}m"

/**
 * The week.
 *
 * Seven rows, today first, each showing the stretch of daylight and the two times
 * a person actually plans around. A bar for the day length rather than a number:
 * it makes the season legible at a glance, which is the thing a sunrise/sunset
 * table is really for.
 */
@Composable
private fun WeekPanel(state: UiState, sky: SkyPalette, accent: Color) {
    val week = state.week
    if (week.isEmpty()) return

    val longest = week.maxOf { it.daylightMinutes }.coerceAtLeast(1)

    GlassCard(sky) {
        Column(Modifier.fillMaxWidth().padding(18.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "THE WEEK",
                    color = SkyInkFaint,
                    fontSize = 11.sp,
                    letterSpacing = 1.6.sp,
                    modifier = Modifier.weight(1f)
                )
                Text(
                    text = "sunrise · sunset",
                    color = SkyInkFaint,
                    fontSize = 11.sp
                )
            }
            Spacer(Modifier.height(10.dp))
            week.forEachIndexed { index, day ->
                if (index > 0) {
                    Box(
                        Modifier
                            .fillMaxWidth()
                            .height(1.dp)
                            .background(Color.White.copy(alpha = 0.07f))
                    )
                }
                WeekRow(day, longest, accent, isToday = index == 0)
            }
        }
    }
}

@Composable
private fun WeekRow(
    day: app.namaz.azan.core.DayTimes,
    longest: Int,
    accent: Color,
    isToday: Boolean
) {
    val sunrise = day.of(app.namaz.azan.core.Prayer.SUNRISE)
    val sunset = day.of(app.namaz.azan.core.Prayer.MAGHRIB)
    val dow = day.date.dayOfWeek.name.take(3)
        .lowercase().replaceFirstChar { it.uppercase() }

    Row(
        Modifier.fillMaxWidth().padding(vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = if (isToday) "Today" else dow,
            color = if (isToday) SkyInk else SkyInkDim,
            fontSize = 13.sp,
            fontWeight = if (isToday) FontWeight.SemiBold else FontWeight.Normal,
            modifier = Modifier.width(56.dp)
        )
        Text(
            text = sunrise?.let { format(it) } ?: "—",
            color = SkyInkDim,
            fontSize = 13.sp,
            modifier = Modifier.width(50.dp)
        )
        // the day-length bar, scaled to the longest day of the week
        Box(
            Modifier
                .weight(1f)
                .height(3.dp)
                .clip(RoundedCornerShape(2.dp))
                .background(Color.White.copy(alpha = 0.10f))
        ) {
            Box(
                Modifier
                    .fillMaxWidth((day.daylightMinutes.toFloat() / longest).coerceIn(0.35f, 1f))
                    .height(3.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(if (isToday) accent.copy(alpha = 0.85f)
                                else Color.White.copy(alpha = 0.38f))
            )
        }
        Text(
            text = sunset?.let { format(it) } ?: "—",
            color = SkyInkDim,
            fontSize = 13.sp,
            textAlign = TextAlign.End,
            modifier = Modifier.width(50.dp)
        )
    }
}

/**
 * Qibla.
 *
 * A compass rose with the bearing drawn on it, the bearing in degrees, and the
 * sentence that makes it usable: this is true north, so the phone's own compass
 * will differ by the local magnetic declination. Rather than model that
 * declination and pretend, the app says it.
 */
@Composable
private fun QiblaPanel(state: UiState, sky: SkyPalette, accent: Color) {
    GlassCard(sky) {
        Row(
            Modifier.fillMaxWidth().padding(18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            QiblaCompass(
                bearingDegrees = state.qibla,
                palette = sky,
                accent = accent,
                modifier = Modifier.size(96.dp)
            )
            Spacer(Modifier.width(18.dp))
            Column {
                Text(
                    text = "QIBLA",
                    color = SkyInkFaint,
                    fontSize = 11.sp,
                    letterSpacing = 1.6.sp
                )
                Spacer(Modifier.height(6.dp))
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(
                        text = "%.1f".format(state.qibla),
                        color = SkyInk,
                        fontSize = 34.sp,
                        fontWeight = FontWeight.Light,
                        letterSpacing = (-1).sp
                    )
                    Text(
                        text = "°",
                        color = SkyInkDim,
                        fontSize = 20.sp,
                        modifier = Modifier.padding(bottom = 5.dp)
                    )
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "from true north",
                    color = SkyInkDim,
                    fontSize = 12.sp
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "not magnetic — allow for declination",
                    color = SkyInkFaint,
                    fontSize = 10.sp
                )
            }
        }
    }
}

/**
 * Credit, and a door out.
 *
 * Placed last, above the promise, because it belongs at the foot of the screen —
 * but given a card rather than a line of grey text, because a typed URL is the
 * one thing a person will not do and a card is the one thing they will tap.
 *
 * This is the only UI in the app that leaves the device. See
 * [app.namaz.azan.data.Credits] for why every claim on it is quoted from the site.
 */
@Composable
private fun MadeByCard(sky: SkyPalette, onOpenWebsite: () -> Unit) {
    val shape = RoundedCornerShape(22.dp)
    Row(
        Modifier
            .fillMaxWidth()
            .clip(shape)
            .background(sky.glass())
            .border(
                1.dp,
                Brush.verticalGradient(
                    0f to sky.hairlineStrong(),
                    1f to Color.White.copy(alpha = 0.04f)
                ),
                shape
            )
            // The whole card is the target, not just the text: a 48 dp-tall row is
            // a far better hit area than a URL.
            .clickable(onClick = onOpenWebsite)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // A small mark: a bracket pair, which is what the site is about — the code.
        Box(
            Modifier
                .size(38.dp)
                .clip(RoundedCornerShape(11.dp))
                .background(Color.White.copy(alpha = 0.10f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "</>",
                color = SunGold,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = (-0.5).sp
            )
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(
                text = app.namaz.azan.data.Credits.MADE_BY,
                color = SkyInk,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = app.namaz.azan.data.Credits.TAGLINE,
                color = SkyInkDim,
                fontSize = 11.sp
            )
        }
        Spacer(Modifier.width(8.dp))
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = app.namaz.azan.data.Credits.WEBSITE_LABEL,
                color = SunGold,
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium
            )
            Spacer(Modifier.height(2.dp))
            // An arrow made of type, so there is no icon dependency here.
            Text(
                text = "open ↗",
                color = SkyInkFaint,
                fontSize = 10.sp
            )
        }
    }
}

/**
 * The promise, in one line, at the bottom where it can be read without being in
 * the way. It is the thing that distinguishes this app from every other one in
 * the category, so it earns its place on the first screen.
 */
@Composable
private fun Footer(state: UiState) {
    Column(
        Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "${state.method.label}  ·  ${state.madhab.label} Asr",
            color = SkyInkFaint,
            fontSize = 11.sp,
            letterSpacing = 0.3.sp,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(5.dp))
        Text(
            // "one link" rather than "no network": the app makes no request, but it
            // can hand a URL to the browser, and the line should not claim otherwise.
            text = "Works offline · no account · no ads · one link, opened in your browser",
            color = SkyInkFaint.copy(alpha = 0.75f),
            fontSize = 10.sp,
            textAlign = TextAlign.Center
        )
    }
}

/**
 * The one card shape in the app.
 *
 * A glass fill, a hairline, and a very soft outer edge. Deliberately not a
 * Material card: an elevated surface with a shadow is a light source pointing the
 * wrong way on a screen that already has a sun on it. The hairline is the
 * gradient-brushed white edge that makes glass read as glass on a dark ground.
 */
@Composable
fun GlassCard(
    sky: SkyPalette,
    hero: Boolean = false,
    content: @Composable () -> Unit
) {
    val shape = RoundedCornerShape(if (hero) 26.dp else 22.dp)
    Box(
        Modifier
            .fillMaxWidth()
            .clip(shape)
            .background(if (hero) sky.glassHero() else sky.glass())
            .border(
                width = 1.dp,
                brush = Brush.verticalGradient(
                    0f to (if (hero) sky.hairlineStrong() else sky.hairline()),
                    1f to Color.White.copy(alpha = 0.04f)
                ),
                shape = shape
            )
    ) {
        content()
    }
}

private fun format(time: PrayerTime): String = formatClock(time.time)

/** LocalTime -> "HH:MM". Used for the night times, which are not prayer instants. */
private fun formatClock(time: java.time.LocalTime): String =
    "%02d:%02d".format(time.hour, time.minute)

private fun formatDuration(minutes: Int): String {
    val h = minutes / 60
    val m = minutes % 60
    return "${h} h ${m.toString().padStart(2, '0')} m of night"
}
