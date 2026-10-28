package com.expensahouse.app.ui.components

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import com.expensahouse.app.data.remote.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.URL


@Composable
internal fun OfferImage(url: String?, name: String) {
    var bitmap by remember(url) { mutableStateOf<Bitmap?>(null) }
    LaunchedEffect(url) {
        if (url?.startsWith("https://") == true || url?.startsWith("http://") == true) {
            bitmap = withContext(Dispatchers.IO) {
                runCatching {
                    val connection = URL(url).openConnection().apply { connectTimeout = 5000; readTimeout = 5000 }
                    connection.getInputStream().use { BitmapFactory.decodeStream(it) }
                }.getOrNull()
            }
        }
    }
    val loaded = bitmap
    if (loaded != null) Image(loaded.asImageBitmap(), name, modifier = Modifier.fillMaxWidth().height(100.dp))
    else Text("📦 Imagen no disponible")
}
