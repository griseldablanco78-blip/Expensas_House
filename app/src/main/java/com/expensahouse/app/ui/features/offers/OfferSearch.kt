package com.expensahouse.app.ui.features.offers

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.expensahouse.app.data.remote.*
import kotlinx.coroutines.launch

import com.expensahouse.app.core.di.AppContainer
import com.expensahouse.app.ui.components.VoiceOutlinedTextField
import com.expensahouse.app.ui.components.OfferImage
import com.expensahouse.app.ui.components.errorText

@Composable
internal fun ConnectedOfferSearch(initialQuery: String = "", repository: com.expensahouse.app.data.repository.OffersRepository = AppContainer.offersRepository) {
    var query by remember(initialQuery) { mutableStateOf(initialQuery) }
    var sort by remember { mutableStateOf("discount") }
    var result by remember { mutableStateOf<Comparison?>(null) }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val uri = LocalUriHandler.current
    fun search() {
        if (busy || query.isBlank()) return
        busy = true
        scope.launch {
            try { result = repository.compare(query, sort); status = result?.warning.orEmpty() }
            catch (error: Exception) { result = null; status = errorText(error) }
            finally { busy = false }
        }
    }
    LaunchedEffect(initialQuery) { if (initialQuery.isNotBlank()) search() }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        VoiceOutlinedTextField(value = query, onValueChange = { query = it }, label = { Text("Producto o consulta por voz") })
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            FilterChip(selected = sort == "discount", onClick = { sort = "discount" }, label = { Text("Mayor descuento") })
            FilterChip(selected = sort == "price", onClick = { sort = "price" }, label = { Text("Menor precio") })
        }
        Button(onClick = { search() }, enabled = !busy && query.isNotBlank()) { Text(if (busy) "Buscando…" else "Buscar oferta top") }
        if (status.isNotBlank()) Text(status)
        result?.let { comparison ->
            if (comparison.offers.isEmpty()) Text("No hay ofertas coincidentes con precio.")
            comparison.offers.take(10).forEachIndexed { index, offer ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        if (index == 0) Text("🏆 Oferta top según el filtro elegido")
                        OfferImage(offer.image_url, offer.product)
                        Text(offer.product, style = MaterialTheme.typography.titleMedium)
                        Text("${offer.store} · $${String.format("%.2f", offer.promo_price)}")
                        Text(offer.promo_text)
                        if (!offer.conditions.isNullOrBlank()) Text(offer.conditions)
                        Text("Fuente: ${offer.source.orEmpty()}")
                        if (offer.direct_link?.startsWith("https://") == true) TextButton(onClick = { uri.openUri(offer.direct_link) }) { Text("Ver en supermercado") }
                    }
                }
            }
        }
        TextButton(onClick = { uri.openUri("https://ratoneando.ar/?q=" + java.net.URLEncoder.encode(query, "UTF-8")) }) { Text("Consultar en Ratoneando ↗") }
    }
}
