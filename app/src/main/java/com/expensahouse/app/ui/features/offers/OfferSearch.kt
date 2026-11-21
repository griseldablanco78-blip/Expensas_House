package com.expensahouse.app.ui.features.offers

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import com.expensahouse.app.data.remote.*
import kotlinx.coroutines.launch

import com.expensahouse.app.core.di.AppContainer
import com.expensahouse.app.ui.components.VoiceOutlinedTextField
import com.expensahouse.app.ui.components.OfferImage
import com.expensahouse.app.ui.components.errorText

@Composable
internal fun ConnectedOfferSearch(initialQuery: String = "", repository: com.expensahouse.app.data.repository.OffersRepository = AppContainer.offersRepository) {
    var query by remember(initialQuery) { mutableStateOf(initialQuery) }
    var result by remember { mutableStateOf<Comparison?>(null) }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var searchSequence by remember { mutableStateOf(0) }
    val scope = rememberCoroutineScope()
    val uri = LocalUriHandler.current
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    var showSourceInfo by remember { mutableStateOf(false) }
    fun search() {
        if (query.isBlank()) return
        val submitted = query.trim()
        val sequence = ++searchSequence
        focus.clearFocus(); keyboard?.hide()
        busy = true
        result = null
        scope.launch {
            try {
                val response = repository.compare(submitted, "price")
                if (sequence == searchSequence) { result = response; status = response.warning.orEmpty() }
            } catch (error: kotlinx.coroutines.CancellationException) { throw error }
            catch (error: Exception) { if (sequence == searchSequence) { result = null; status = errorText(error) } }
            finally { if (sequence == searchSequence) busy = false }
        }
    }
    LaunchedEffect(initialQuery) { if (initialQuery.isNotBlank()) search() }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        VoiceOutlinedTextField(value = query, onValueChange = { query = it; result = null; status = ""; searchSequence++; busy = false }, label = { Text("Producto o consulta por voz") })
        Button(onClick = { search() }, enabled = !busy && query.isNotBlank()) { Text(if (busy) "Buscando…" else "Buscar oferta top") }
        if (status.isNotBlank()) {
            TextButton(onClick = { showSourceInfo = !showSourceInfo }) { Text(if (showSourceInfo) "Ocultar información de fuentes" else "Información de fuentes") }
            if (showSourceInfo || result == null) Text(status)
        }
        result?.let { comparison ->
            var visible by remember(comparison) { mutableStateOf(10) }
            val ordered = comparison.offers.sortedWith(compareBy<ProductOffer>({ !it.size_confirmed }, { it.promo_price }))
            Text("${ordered.size} ofertas · de menor a mayor precio", style = MaterialTheme.typography.labelMedium)
            if (comparison.offers.isEmpty()) Text("No hay ofertas coincidentes con precio.")
            ordered.take(visible).chunked(2).forEach { pair ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    pair.forEach { offer ->
                        key(offer.id.ifBlank { "${offer.store}:${offer.product}" }) {
                            CompactOfferCard(offer, offer.id == comparison.top_offer?.id, Modifier.weight(1f))
                        }
                    }
                    if (pair.size == 1) Spacer(Modifier.weight(1f))
                }
            }
            if (comparison.offers.size > visible) TextButton(onClick = { visible += 10 }) { Text("Ver más ofertas (${visible.coerceAtMost(comparison.offers.size)} de ${comparison.offers.size})") }
        }
        TextButton(onClick = { uri.openUri("https://ratoneando.ar/?q=" + java.net.URLEncoder.encode(query, "UTF-8")) }) { Text("Consultar en Ratoneando ↗") }
    }
}

@Composable
private fun CompactOfferCard(offer: ProductOffer, isTop: Boolean, modifier: Modifier) {
    var expanded by remember(offer.id) { mutableStateOf(false) }
    val uri = LocalUriHandler.current
    Card(modifier) {
        Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(offer.store, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (isTop) Text("🏆 Menor precio", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
            OfferImage(offer.image_url, offer.product)
            Text(offer.product, style = MaterialTheme.typography.bodySmall, maxLines = if (expanded) Int.MAX_VALUE else 2, overflow = TextOverflow.Ellipsis)
            Text(offerMoney(offer.promo_price), style = MaterialTheme.typography.titleMedium)
            if (!offer.size_confirmed) Text("Tamaño sin confirmar", style = MaterialTheme.typography.labelSmall)
            TextButton(onClick = { expanded = !expanded }, contentPadding = PaddingValues(0.dp)) { Text(if (expanded) "Cerrar detalle" else "Ver detalle") }
            if (expanded) {
                Text(offer.promo_text, style = MaterialTheme.typography.bodySmall)
                if (!offer.conditions.isNullOrBlank()) Text(offer.conditions, style = MaterialTheme.typography.bodySmall)
                Text("Fuente: ${offer.source.orEmpty()}", style = MaterialTheme.typography.bodySmall)
                Text(if (offer.size_confirmed) "Presentación coincidente" else "Presentación sin confirmar", style = MaterialTheme.typography.bodySmall)
                offer.updated_at?.takeIf { it.isNotBlank() }?.let { Text("Consulta: ${it.take(19).replace('T',' ')}", style = MaterialTheme.typography.bodySmall) }
                if (offer.direct_link?.startsWith("https://") == true) TextButton(onClick = { uri.openUri(offer.direct_link) }, contentPadding = PaddingValues(0.dp)) { Text("Ir a la tienda ↗") }
            }
        }
    }
}

private fun offerMoney(value: Double): String = java.text.NumberFormat.getCurrencyInstance(java.util.Locale("es","AR")).format(value)
