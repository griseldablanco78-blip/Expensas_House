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
            var visible by remember(comparison) { mutableStateOf(10) }
            val analysis = comparison.ai_analysis
            val cheapest = comparison.offers.minByOrNull { it.promo_price }
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text("Resumen de la comparación", style = MaterialTheme.typography.titleMedium)
                    Text("${comparison.offers.size} ofertas · ${comparison.cleaned_query ?: query}")
                    if (analysis?.best_single != null) Text("Menor precio publicado: ${analysis.best_single.store} · ${offerMoney(analysis.best_single.price)}")
                    else if (cheapest != null) Text("Menor precio publicado: ${cheapest.store} · ${offerMoney(cheapest.promo_price)}")
                    val saving = analysis?.max_saving_percent ?: comparison.offers.maxOfOrNull { it.saving_percent } ?: 0.0
                    Text(if (saving > 0) "Mayor descuento comparable: ${String.format(java.util.Locale("es","AR"),"%.2f",saving)}%" else "Sin descuento informado")
                    analysis?.verdict?.takeIf { it.isNotBlank() }?.let { Text(it) }
                    analysis?.stock_alert?.takeIf { it.isNotBlank() }?.let { Text(it) }
                    Text("Compará la misma presentación y revisá las condiciones antes de comprar.")
                }
            }
            if (comparison.offers.isEmpty()) Text("No hay ofertas coincidentes con precio.")
            comparison.offers.take(visible).forEachIndexed { index, offer ->
              key(offer.id.ifBlank { "${offer.store}:${offer.product}:$index" }) {
                var expanded by remember { mutableStateOf(false) }
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        if (index == 0) Text("🏆 Oferta top según el filtro elegido")
                        OfferImage(offer.image_url, offer.product)
                        Text(offer.product, style = MaterialTheme.typography.titleMedium)
                        Text("${offer.store} · ${offerMoney(offer.promo_price)}")
                        Text(offer.promo_text)
                        if (!offer.conditions.isNullOrBlank()) Text(offer.conditions)
                        Text("Fuente: ${offer.source.orEmpty()}")
                        TextButton(onClick = { expanded = !expanded }) { Text(if (expanded) "Ocultar detalle" else "Ver detalle") }
                        if (expanded) {
                            Text("Marca: ${offer.brand?.takeIf { it.isNotBlank() } ?: "No informada"}")
                            Text("Precio publicado: ${offerMoney(offer.promo_price)}")
                            Text(if (offer.size_confirmed) "Presentación coincidente con la consulta" else "Presentación sin confirmar")
                            offer.unit?.takeIf { it.isNotBlank() }?.let { Text("Unidad: $it") }
                            offer.unit_price?.takeIf { it > 0 }?.let { Text("Precio por unidad de referencia: ${offerMoney(it)}") }
                            offer.updated_at?.takeIf { it.isNotBlank() }?.let { Text("Consulta de la fuente: ${it.take(19).replace('T',' ')}") }
                            if (offer.promo_type == "bulk") Text("La promoción requiere varias unidades; el descuento comparable no se aplica a una sola unidad.")
                            Text("Vigencia y disponibilidad: confirmar en el supermercado.")
                        }
                        if (offer.direct_link?.startsWith("https://") == true) TextButton(onClick = { uri.openUri(offer.direct_link) }) { Text("Ver en supermercado") }
                    }
                }
              }
            }
            if (comparison.offers.size > visible) TextButton(onClick = { visible += 10 }) { Text("Ver más ofertas (${visible.coerceAtMost(comparison.offers.size)} de ${comparison.offers.size})") }
        }
        TextButton(onClick = { uri.openUri("https://ratoneando.ar/?q=" + java.net.URLEncoder.encode(query, "UTF-8")) }) { Text("Consultar en Ratoneando ↗") }
    }
}

private fun offerMoney(value: Double): String = java.text.NumberFormat.getCurrencyInstance(java.util.Locale("es","AR")).format(value)
