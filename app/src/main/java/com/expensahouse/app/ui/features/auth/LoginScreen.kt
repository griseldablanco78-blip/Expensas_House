package com.expensahouse.app.ui.features.auth

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.expensahouse.app.core.auth.*
import com.expensahouse.app.data.remote.ExpensaApiClient
import com.expensahouse.app.ui.components.errorText
import com.expensahouse.app.ui.theme.ExpensaHouseTheme
import kotlinx.coroutines.launch

@Composable
internal fun AccountGate(beforeSessionChange: () -> Unit, content: @Composable () -> Unit) {
    val user by AuthSession.user.collectAsState()
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    var action by remember { mutableStateOf("login") }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    if (user?.role != null) { content(); return }
    ExpensaHouseTheme {
        Surface(Modifier.fillMaxSize()) {
            Column(Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Expensa House", style = MaterialTheme.typography.headlineMedium)
                Text("Iniciá sesión con tu usuario y contraseña. La administradora asigna el acceso al hogar.")
                if (user != null) {
                    Text("Tu cuenta está creada, pero todavía no tenés acceso al hogar. Pedile a la administradora que asigne tu permiso.")
                    Button(onClick = { beforeSessionChange(); AuthSession.clear() }) { Text("Volver al inicio de sesión") }
                } else {
                    listOf("login" to "Iniciar sesión", "register" to "Crear cuenta").forEach { (value, label) ->
                        FilterChip(selected = action == value, onClick = { action = value; status = "" }, label = { Text(label) }, enabled = !busy)
                    }
                    if (action !in setOf("verify", "reset")) OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("Usuario") }, singleLine = true, enabled = !busy)
                    if (action in setOf("verify", "reset")) OutlinedTextField(value = code, onValueChange = { code = it }, label = { Text("Código recibido por correo") }, enabled = !busy)
                    if (action !in setOf("resend", "forgot")) {
                        OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Contraseña") }, visualTransformation = PasswordVisualTransformation(), singleLine = true, enabled = !busy)
                        if (action != "login") Text("Usá una frase de al menos 15 caracteres. Después de crear la cuenta, iniciá sesión.")
                    }
                    Button(enabled = !busy, onClick = {
                        busy = true
                        scope.launch {
                            try {
                                val api = ExpensaApiClient.service
                                val response = when (action) {
                                    "register" -> api.register(RegisterRequest(email.trim(), password))
                                    "verify" -> api.verifyEmail(VerifyRequest(code.trim(), password))
                                    "resend" -> api.resendVerification(EmailRequest(email.trim()))
                                    "forgot" -> api.forgotPassword(EmailRequest(email.trim()))
                                    "reset" -> api.resetPassword(VerifyRequest(code.trim(), password))
                                    else -> api.login(LoginRequest(email.trim(), password))
                                }
                                if (response.access_token != null && response.user != null) {
                                    beforeSessionChange(); AuthSession.start(response)
                                } else { status = response.message.orEmpty(); if (action in setOf("verify", "reset")) action = "login" }
                                password = ""
                            } catch (error: Exception) { status = errorText(error) }
                            finally { busy = false }
                        }
                    }) { Text(if (busy) "Procesando…" else "Continuar") }
                }
                if (status.isNotBlank()) Text(status)
            }
        }
    }
}


@Composable
internal fun ChangePasswordDialog(onDismiss: () -> Unit) {
    var current by remember { mutableStateOf("") }
    var next by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    AlertDialog(
        onDismissRequest = { if (!busy) onDismiss() },
        title = { Text("Cambiar contraseña") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Usá al menos 15 caracteres. Se cerrarán todas tus sesiones.")
                OutlinedTextField(current, { current = it }, label = { Text("Contraseña actual") }, visualTransformation = PasswordVisualTransformation(), enabled = !busy, singleLine = true)
                OutlinedTextField(next, { next = it }, label = { Text("Nueva contraseña") }, visualTransformation = PasswordVisualTransformation(), enabled = !busy, singleLine = true)
                OutlinedTextField(confirmation, { confirmation = it }, label = { Text("Repetir contraseña") }, visualTransformation = PasswordVisualTransformation(), enabled = !busy, singleLine = true)
                if (status.isNotBlank()) Text(status)
            }
        },
        confirmButton = {
            TextButton(enabled = !busy, onClick = {
                if (next != confirmation) { status = "Las contraseñas no coinciden." }
                else if (next.length !in 15..128) { status = "Usá entre 15 y 128 caracteres." }
                else {
                    busy = true
                    scope.launch {
                        try {
                            ExpensaApiClient.service.changePassword(ChangePasswordRequest(current, next))
                            current = ""; next = ""; confirmation = ""
                            AuthSession.clear(); onDismiss()
                        } catch (error: Exception) { status = errorText(error) }
                        finally { busy = false }
                    }
                }
            }) { Text("Guardar") }
        },
        dismissButton = { TextButton(enabled = !busy, onClick = onDismiss) { Text("Cancelar") } }
    )
}
