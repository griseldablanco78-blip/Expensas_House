package com.expensahouse.app.ui.features.chat

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.expensahouse.app.data.remote.*
import kotlinx.coroutines.launch

import com.expensahouse.app.core.di.AppContainer
import com.expensahouse.app.ui.components.VoiceOutlinedTextField
import com.expensahouse.app.ui.components.OfferImage
import com.expensahouse.app.ui.components.errorText

@Composable
internal fun ConnectedChatDialog(onDismiss: () -> Unit, onNavigate: (Int, String?) -> Unit, repository: com.expensahouse.app.data.repository.ChatRepository = AppContainer.chatRepository) {
    var query by remember { mutableStateOf("") }
    var answer by remember { mutableStateOf<ChatAnswer?>(null) }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var context by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    fun send(message: String) {
        if (busy || message.isBlank()) return
        busy = true
        scope.launch {
            try { answer = repository.chat(ChatRequest(message, context)); context = answer?.context; status = "" }
            catch (error: Exception) { status = errorText(error) }
            finally { busy = false }
        }
    }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Boti House") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("1 · Ofertas", "2 · Presupuesto", "3 · Faltantes").forEachIndexed { index, label ->
                OutlinedButton(onClick = { send((index + 1).toString()) }, enabled = !busy) { Text(label) }
            }
            VoiceOutlinedTextField(value = query, onValueChange = { query = it }, label = { Text("Escribí o dictá tu consulta") })
            Button(onClick = { send(query) }, enabled = !busy) { Text(if (busy) "Consultando…" else "Consultar") }
            if (status.isNotBlank()) Text(status)
            answer?.let { response ->
                Text(response.answer)
                response.comparison?.offers?.firstOrNull()?.let { offer ->
                    OfferImage(offer.image_url, offer.product)
                    Text("${offer.product} · ${offer.store}")
                }
                response.action?.let { action ->
                    TextButton(onClick = { onNavigate(if (action == "stock") 1 else 4, if (response.comparison != null) query else null) }) { Text("Ir a la sección") }
                }
            }
        }
    }, confirmButton = { TextButton(onClick = onDismiss) { Text("Cerrar") } })
}
