package app.namaz.azan.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.namaz.azan.core.DayTimes
import app.namaz.azan.core.Prayer
import app.namaz.azan.ui.theme.SkyInk
import app.namaz.azan.ui.theme.SkyInkDim
import app.namaz.azan.ui.theme.SkyInkFaint
import app.namaz.azan.ui.theme.accent

/**
 * The month, as a printed timetable would show it.
 *
 * This is the screen a mosque puts on the wall, and it exists here for the same
 * reason: somebody wants to know the time for a date that is not today. Every row
 * is the same computation the home screen uses, so the two can never disagree.
 *
 * Fajr through Isha, with the Hijri date in the margin where the printed sheets
 * put it, and today marked rather than hidden.
 */
@Composable
fun TimetableScreen(
    state: UiState,
    onBack: () -> Unit
) {
    val sky = state.sky
    val month = state.month
    val zone = state.zone

    Box(
        Modifier
            .fillMaxSize()
            .background(sky.ground)
    ) {
        SkyCanvas(
            palette = sky,
            sunAltitude = state.sunAltitude,
            sunAzimuth = state.sunAzimuth,
            modifier = Modifier.fillMaxSize()
        )

        Column(
            Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .padding(horizontal = 16.dp)
        ) {
            Row(
                Modifier.fillMaxWidth().padding(top = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onBack) {
                    Icon(
                        Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Back",
                        tint = SkyInk
                    )
                }
                Column(Modifier.weight(1f)) {
                    Text(
                        text = month.firstOrNull()?.let { m ->
                            val d = m.date
                            "${d.month.name.lowercase().replaceFirstChar { it.uppercase() }} ${d.year}"
                        } ?: "Timetable",
                        color = SkyInk,
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "${state.cityName}  ·  ${state.method.label}",
                        color = SkyInkFaint,
                        fontSize = 11.sp
                    )
                }
            }

            Spacer(Modifier.height(6.dp))
            // column headings, aligned with the rows below
            Row(
                Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                HeaderCell("DATE", 46.dp)
                HeaderCell("H", 28.dp)
                Prayer.entries.forEach { prayer ->
                    HeaderCellWeighted(prayer.label.take(3).uppercase())
                }
            }
            Box(
                Modifier.fillMaxWidth().height(1.dp)
                    .background(Color.White.copy(alpha = 0.14f))
            )

            LazyColumn(Modifier.weight(1f)) {
                items(month) { day ->
                    TimetableRow(day, isToday = day.date == state.day?.date, accent = sky.accent())
                }
            }

            Text(
                text = "Times are computed on this phone. Confirm with your mosque.",
                color = SkyInkFaint,
                fontSize = 10.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(vertical = 10.dp)
            )
        }
    }
}

@Composable
private fun HeaderCell(text: String, width: androidx.compose.ui.unit.Dp) {
    Text(
        text = text,
        color = SkyInkFaint,
        fontSize = 9.sp,
        letterSpacing = 0.5.sp,
        textAlign = TextAlign.Center,
        modifier = Modifier.width(width)
    )
}

/**
 * The same heading, but taking an equal share of the row.
 *
 * `Modifier.weight` only exists inside a RowScope, so this has to be an extension
 * on RowScope rather than a parameter the caller passes in.
 */
@Composable
private fun androidx.compose.foundation.layout.RowScope.HeaderCellWeighted(text: String) {
    Text(
        text = text,
        color = SkyInkFaint,
        fontSize = 9.sp,
        letterSpacing = 0.5.sp,
        textAlign = TextAlign.Center,
        modifier = Modifier.weight(1f)
    )
}

@Composable
private fun TimetableRow(day: DayTimes, isToday: Boolean, accent: Color) {
    val hijri = day.hijri
    Row(
        Modifier
            .fillMaxWidth()
            .then(
                if (isToday) Modifier.background(accent.copy(alpha = 0.14f))
                else Modifier
            )
            .padding(horizontal = 10.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "%02d".format(day.date.dayOfMonth),
            color = if (isToday) SkyInk else SkyInkDim,
            fontSize = 12.sp,
            fontWeight = if (isToday) FontWeight.Bold else FontWeight.Normal,
            textAlign = TextAlign.Center,
            modifier = Modifier.width(46.dp)
        )
        // the Hijri day, small, where a printed sheet puts it
        Text(
            text = hijri?.day?.toString() ?: "",
            color = SkyInkFaint,
            fontSize = 9.sp,
            textAlign = TextAlign.Center,
            modifier = Modifier.width(28.dp)
        )
        Prayer.entries.forEach { prayer ->
            val t = day.of(prayer)
            Text(
                text = t?.let { "%02d:%02d".format(it.time.hour, it.time.minute) } ?: "—",
                color = if (prayer == Prayer.SUNRISE) SkyInkFaint else SkyInk,
                fontSize = 11.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.weight(1f)
            )
        }
    }
    Box(
        Modifier.fillMaxWidth().height(1.dp)
            .background(Color.White.copy(alpha = 0.05f))
    )
}
