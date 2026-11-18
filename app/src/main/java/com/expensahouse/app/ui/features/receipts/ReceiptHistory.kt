package com.expensahouse.app.ui.features.receipts

import androidx.compose.foundation.layout.*
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

@Composable
internal fun ConnectedReceiptHistory(refreshKey: Int = 0, repository: ReceiptsRepository = AppContainer.receiptsRepository) {
    var receipts by remember { mutableStateOf<List<ReceiptSummary>>(emptyList()) }
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
            Text("Resumen de compras y precios históricos", style = MaterialTheme.typography.titleMedium)
            Text("Los precios corresponden a la fecha de compra guardada.")
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
                Text("${receipt.date()} · ${receipt.store ?: receipt.note ?: "Sin supermercado"}", style = MaterialTheme.typography.titleSmall)
                receipt.items.orEmpty().forEach { product ->
                    Text(product.description)
                    Text("Cantidad: ${product.quantity} · Precio unitario: ${money.format(product.unit_price)}")
                    Text("Descuento: ${money.format(product.discount)} · Neto: ${money.format(product.line_total)}")
                }
                if (receipt.items.isNullOrEmpty()) Text("Este gasto no tiene productos detallados guardados.")
                Text("IVA: ${receipt.vat_amount?.let { money.format(it) } ?: "No informado"} (${if (receipt.vat_included) "incluido" else "separado"})")
                Text("Total pagado: ${money.format(receipt.amount)}")
                HorizontalDivider()
            }
        }
    }
}
