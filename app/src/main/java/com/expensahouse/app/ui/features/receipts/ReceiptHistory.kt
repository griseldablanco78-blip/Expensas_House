package com.expensahouse.app.ui.features.receipts

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.expensahouse.app.core.di.AppContainer
import com.expensahouse.app.data.remote.ReceiptSummary
import com.expensahouse.app.data.repository.ReceiptsRepository
import com.expensahouse.app.ui.components.errorText
import java.time.Instant
import java.time.ZoneId
import java.text.NumberFormat
import java.util.Locale

@Composable
internal fun ReceiptActions(onScan: () -> Unit, onManual: () -> Unit) {
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Button(onClick = onScan, modifier = Modifier.fillMaxWidth()) { Text("Cargar ticket · foto o galería") }
        TextButton(onClick = onManual, modifier = Modifier.fillMaxWidth()) { Text("Registrar gasto manual") }
    }
}

private fun ReceiptSummary.date(): String = purchase_date ?: timestamp?.let {
    Instant.ofEpochMilli(it).atZone(ZoneId.of("America/Argentina/Buenos_Aires")).toLocalDate().toString()
} ?: "Sin fecha"

@OptIn(ExperimentalFoundationApi::class)
@Composable
internal fun ConnectedReceiptHistory(refreshKey: Int = 0, repository: ReceiptsRepository = AppContainer.receiptsRepository) {
    var receipts by remember { mutableStateOf<List<ReceiptSummary>>(emptyList()) }
    var selected by remember { mutableStateOf<ReceiptSummary?>(null) }
    var selectedDate by remember { mutableStateOf("") }
    var menu by remember { mutableStateOf(false) }
    var retry by remember { mutableStateOf(0) }
    var busy by remember { mutableStateOf(true) }
    var status by remember { mutableStateOf("") }
    LaunchedEffect(refreshKey, retry) {
        busy = true
        try { receipts = repository.history(); status = "" }
        catch (error: Exception) { status = errorText(error) }
        finally { busy = false }
    }
    val money = remember { NumberFormat.getCurrencyInstance(Locale("es", "AR")) }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Tickets guardados", style = MaterialTheme.typography.titleMedium)
            Text("Doble toque para abrir", style = MaterialTheme.typography.labelSmall)
            if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (status.isNotBlank()) Text(status)
            TextButton(onClick = { retry++ }, enabled = !busy) { Text("Actualizar resúmenes") }
            Box {
                TextButton(onClick = { menu = true }) { Text(if (selectedDate.isBlank()) "Elegir fecha del resumen" else "Fecha: $selectedDate") }
                DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                    DropdownMenuItem(text = { Text("Todas las fechas") }, onClick = { selectedDate = ""; menu = false })
                    receipts.map { it.date() }.distinct().sortedDescending().forEach { date ->
                        DropdownMenuItem(text = { Text(date) }, onClick = { selectedDate = date; menu = false })
                    }
                }
            }
            val visible = receipts.filter { selectedDate.isBlank() || it.date() == selectedDate }.sortedByDescending { it.date() }
            if (!busy && visible.isEmpty() && status.isBlank()) Text("No hay compras guardadas para esta fecha.")
            visible.forEach { receipt ->
                OutlinedCard(modifier = Modifier.fillMaxWidth().combinedClickable(
                    onClick = {}, onDoubleClick = { selected = receipt },
                    onLongClick = { selected = receipt }, onLongClickLabel = "Abrir ticket")) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(receipt.store?.takeIf { it.isNotBlank() } ?: receipt.note ?: "Comercio sin nombre", style = MaterialTheme.typography.titleSmall)
                        Text(receipt.date())
                    }
                }
                HorizontalDivider()
            }
        }
    }

    selected?.let { receipt ->
        ReceiptDetail(receipt, repository, onDismiss = { selected = null })
    }
}

@Composable
private fun ReceiptDetail(receipt: ReceiptSummary, repository: ReceiptsRepository, onDismiss: () -> Unit) {
    var image by remember(receipt.id) { mutableStateOf<androidx.compose.ui.graphics.ImageBitmap?>(null) }
    var loading by remember(receipt.id) { mutableStateOf(true) }
    var imageStatus by remember(receipt.id) { mutableStateOf("") }
    val money = remember { NumberFormat.getCurrencyInstance(Locale("es", "AR")) }
    LaunchedEffect(receipt.id) {
        try {
            image = withContext(Dispatchers.IO) {
                val bytes = repository.image(receipt.id)
                requireNotNull(android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)).asImageBitmap()
            }
        } catch (error: Exception) { imageStatus = "No se pudo mostrar la imagen del ticket. Los productos guardados siguen disponibles." }
        finally { loading = false }
    }
    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = MaterialTheme.shapes.large) {
            Column(Modifier.fillMaxWidth().padding(16.dp)) {
                Text(receipt.store ?: receipt.note ?: "Ticket", style = MaterialTheme.typography.titleLarge)
                Column(Modifier.weight(1f, fill = false).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Fecha de compra: ${receipt.date()}")
                    Text("Descontado del presupuesto: ${money.format(receipt.amount)}")
                    receipt.items.orEmpty().forEach { product ->
                        Text(product.description, style = MaterialTheme.typography.titleSmall)
                        Text("Cantidad: ${product.quantity} · Precio unitario: ${money.format(product.unit_price)}")
                        Text("Total: ${money.format(product.line_total)}")
                    }
                    if (receipt.items.isNullOrEmpty()) Text("Este gasto no tiene productos detallados guardados.")
                    if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                    if (imageStatus.isNotBlank()) Text(imageStatus)
                    image?.let { Image(it, contentDescription = "Imagen del ticket guardado", modifier = Modifier.fillMaxWidth()) }
                }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Cerrar detalle") }
            }
        }
    }
}
