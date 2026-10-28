package com.expensahouse.app.ui.features.receipts

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.core.content.FileProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.expensahouse.app.data.remote.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.UUID

import com.expensahouse.app.core.di.AppContainer
import com.expensahouse.app.ui.components.errorText

@Composable
internal fun ConnectedReceiptDialog(onDismiss: () -> Unit, onSaved: () -> Unit, repository: com.expensahouse.app.data.repository.ReceiptsRepository = AppContainer.receiptsRepository) {
    val appContext = LocalContext.current
    val scope = rememberCoroutineScope()
    val storage = remember { appContext.getSharedPreferences("receipt_pending_${com.expensahouse.app.core.auth.AuthSession.user.value?.id}", 0) }
    val gson = remember { com.google.gson.Gson() }
    var pending by remember { mutableStateOf(storage.getString("payload", null)?.let {
        runCatching { gson.fromJson(it, ReceiptCommit::class.java) }.getOrNull()
    }) }
    var text by remember { mutableStateOf(pending?.raw_text ?: "") }
    var receiptImage by remember { mutableStateOf(pending?.receipt_image ?: "") }
    var purchaseDate by remember { mutableStateOf(pending?.purchase_date ?: java.time.LocalDate.now(java.time.ZoneId.of("America/Argentina/Buenos_Aires")).toString()) }
    var store by remember { mutableStateOf(pending?.store ?: "") }
    var items by remember { mutableStateOf(pending?.items ?: emptyList()) }
    var total by remember { mutableStateOf(pending?.total?.toString() ?: "") }
    var adjustment by remember { mutableStateOf(pending?.adjustment_note ?: "") }
    var status by remember { mutableStateOf(if (pending != null) "Ticket pendiente: reintentá el mismo envío para evitar duplicados." else "") }
    var busy by remember { mutableStateOf(false) }
    var draftId by remember { mutableStateOf(UUID.randomUUID().toString()) }
    var capturePath by rememberSaveable { mutableStateOf<String?>(null) }
    var cameraOpen by rememberSaveable { mutableStateOf(false) }
    fun clearCapture() {
        capturePath?.let { path ->
            val file = File(path)
            if (file.parentFile == File(appContext.cacheDir, "ticket_photos")) file.delete()
        }
        capturePath = null
    }
    fun dismiss() {
        if (!busy && !cameraOpen) { clearCapture(); onDismiss() }
    }
    suspend fun interpretReceipt(photo: ByteArray? = null, captured: Boolean = false) {
            try {
                val draft = if (photo != null) repository.scanReceipt(MultipartBody.Part.createFormData("image", "ticket.jpg", RequestBody.create(MediaType.parse("image/jpeg"), photo)))
                            else repository.parseReceipt(ReceiptText(text))
                receiptImage = draft.receipt_image.orEmpty()
                items = draft.items; total = draft.total.toString(); text = draft.raw_text
                draftId = UUID.randomUUID().toString(); status = draft.warnings.joinToString("\n")
                if (captured && draft.items.isNotEmpty()) clearCapture()
            } catch (error: Exception) { status = errorText(error) }
            finally { busy = false }
    }
    fun read() {
        if (busy || pending != null) return
        busy = true
        scope.launch { interpretReceipt() }
    }
    fun loadPhoto(uri: Uri, captured: Boolean = false) {
        if (busy || pending != null) return
        busy = true
        status = "Preparando foto del ticket…"
        scope.launch {
            try {
                val bytes = withContext(Dispatchers.IO) { appContext.contentResolver.openInputStream(uri)?.use { input ->
                    val output = ByteArrayOutputStream()
                    val buffer = ByteArray(8192)
                    while (output.size() <= 10 * 1024 * 1024) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        output.write(buffer, 0, count)
                    }
                    output.toByteArray() } }
                if (bytes == null || bytes.isEmpty()) status = "La foto está vacía. Volvé a sacar la foto."
                else if (bytes.size > 10 * 1024 * 1024) status = "La foto supera 10 MB. Bajá la resolución de la cámara o elegí una foto más pequeña."
                else interpretReceipt(bytes, captured)
            } catch (error: Exception) { status = "No se pudo abrir la foto." }
            finally { busy = false }
        }
    }
    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) loadPhoto(uri)
    }
    val camera = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { saved ->
        cameraOpen = false
        val path = capturePath
        if (saved && path != null) loadPhoto(Uri.fromFile(File(path)), captured = true)
        else { clearCapture(); status = "Captura cancelada. Podés volver a sacar la foto." }
    }
    AlertDialog(onDismissRequest = { dismiss() }, title = { Text("Escanear ticket") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Fotografiá el ticket completo, con buena luz y sin sombras. Se leerán los productos, precios y total para que los revises antes de guardar el gasto.")
            Button(onClick = {
                try {
                    clearCapture()
                    val directory = File(appContext.cacheDir, "ticket_photos").apply { mkdirs() }
                    val photo = File.createTempFile("ticket-", ".jpg", directory)
                    capturePath = photo.absolutePath
                    val uri = FileProvider.getUriForFile(appContext, "${appContext.packageName}.ticketphotos", photo)
                    cameraOpen = true
                    camera.launch(uri)
                } catch (error: Exception) {
                    cameraOpen = false; clearCapture()
                    status = "No se pudo abrir la cámara. Podés elegir una foto de la galería."
                }
            }, enabled = !busy && !cameraOpen && pending == null, modifier = Modifier.fillMaxWidth()) {
                Text("Sacar foto del ticket")
            }
            TextButton(onClick = { photoPicker.launch("image/*") }, enabled = !busy && !cameraOpen && pending == null) { Text("Elegir foto de la galería") }
            if (capturePath != null && !cameraOpen) TextButton(onClick = {
                capturePath?.let { loadPhoto(Uri.fromFile(File(it)), captured = true) }
            }, enabled = !busy && pending == null) { Text("Volver a leer la foto tomada") }
            if (busy) { LinearProgressIndicator(Modifier.fillMaxWidth()); Text("Procesando ticket…") }
            OutlinedTextField(value = text, onValueChange = { text = it }, label = { Text("Texto del ticket") }, enabled = !busy && pending == null)
            TextButton(onClick = { read() }, enabled = !busy && pending == null) { Text("Interpretar texto") }
            if (status.isNotBlank()) Text(status)
            OutlinedTextField(value = purchaseDate, onValueChange = { purchaseDate = it }, label = { Text("Fecha de compra (AAAA-MM-DD)") }, enabled = !busy && pending == null)
            OutlinedTextField(value = store, onValueChange = { store = it }, label = { Text("Supermercado") }, enabled = !busy && pending == null)
            items.forEachIndexed { index, item ->
                OutlinedTextField(value = item.description, onValueChange = { value -> items = items.toMutableList().also { it[index] = item.copy(description = value) } }, label = { Text("Producto ${index + 1}") }, enabled = !busy && pending == null)
                Text("${item.quantity} × $${item.unit_price} = $${item.line_total}")
                Row {
                    ReceiptNumber(item.quantity, "Cantidad", Modifier.weight(1f), !busy && pending == null) { quantity -> items = items.toMutableList().also { it[index] = item.copy(quantity = quantity, line_total = kotlin.math.round(quantity * item.unit_price * 100) / 100) } }
                    ReceiptNumber(item.unit_price, "Precio unidad", Modifier.weight(1f), !busy && pending == null) { price -> items = items.toMutableList().also { it[index] = item.copy(unit_price = price, line_total = kotlin.math.round(item.quantity * price * 100) / 100) } }
                }
                TextButton(onClick = { items = items.filterIndexed { i, _ -> i != index } }, enabled = !busy && pending == null) { Text("Quitar producto") }
            }
            TextButton(onClick = { items = items + ReceiptLine("Producto", 1.0, 1.0, 1.0) }, enabled = !busy && pending == null) { Text("+ Producto") }
            OutlinedTextField(value = total, onValueChange = { total = it }, label = { Text("Total gastado") }, enabled = !busy && pending == null)
            OutlinedTextField(value = adjustment, onValueChange = { adjustment = it }, label = { Text("Ajuste por impuestos o descuentos") }, enabled = !busy && pending == null)
        }
    }, confirmButton = {
        Button(enabled = !busy && (pending != null || (items.isNotEmpty() && store.isNotBlank())), onClick = {
            val amount = total.replace(',', '.').toDoubleOrNull()
            if (pending == null && (amount == null || amount <= 0 || !amount.isFinite())) { status = "Revisá el total."; return@Button }
            if (pending == null && runCatching { java.time.LocalDate.parse(purchaseDate) }.isFailure) { status = "Revisá la fecha (AAAA-MM-DD)."; return@Button }
            val payload = pending ?: ReceiptCommit(draftId, store, items, amount!!, adjustment, purchaseDate, text, receiptImage)
            pending = payload; storage.edit().putString("payload", gson.toJson(payload)).apply(); busy = true
            scope.launch {
                try { repository.confirmReceipt(payload); storage.edit().remove("payload").apply(); pending = null; clearCapture(); onSaved() }
                catch (error: Exception) {
                    if (error is retrofit2.HttpException && error.code() in 400..499) { pending = null; storage.edit().remove("payload").apply() }
                    status = errorText(error) + if (pending != null) " Reintentá el mismo envío." else ""
                } finally { busy = false }
            }
        }) { Text(if (busy) "Procesando…" else "Confirmar gasto") }
    }, dismissButton = { TextButton(onClick = { dismiss() }, enabled = !busy && !cameraOpen) { Text("Cerrar") } })
}


@Composable
private fun ReceiptNumber(value: Double, label: String, modifier: Modifier, enabled: Boolean, onChange: (Double) -> Unit) {
    var text by remember { mutableStateOf(value.toString()) }
    LaunchedEffect(value) { if (text.replace(',', '.').toDoubleOrNull() != value) text = value.toString() }
    OutlinedTextField(value = text, onValueChange = { input ->
        text = input
        input.replace(',', '.').toDoubleOrNull()?.takeIf { it > 0 && it.isFinite() }?.let(onChange)
    }, label = { Text(label) }, modifier = modifier, enabled = enabled)
}
