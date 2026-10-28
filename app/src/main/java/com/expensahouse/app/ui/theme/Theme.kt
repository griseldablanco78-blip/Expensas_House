package com.expensahouse.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

fun expensaColors() = lightColorScheme(
    primary = Leaf,
    onPrimary = Color.White,
    secondary = Sky,
    onSecondary = Color.White,
    tertiary = Gold,
    background = Canvas,
    surface = Color.White,
    onSurface = Ink,
    onBackground = Ink,
    error = Coral,
    onError = Color.White
)

@Composable
fun ExpensaHouseTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = expensaColors(),
        content = content
    )
}
