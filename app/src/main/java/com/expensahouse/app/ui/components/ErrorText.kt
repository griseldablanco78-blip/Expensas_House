package com.expensahouse.app.ui.components

import com.expensahouse.app.BuildConfig
import java.net.ConnectException
import java.net.NoRouteToHostException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

internal fun errorText(error: Exception): String {
    if (error is retrofit2.HttpException) {
        val body = error.response()?.errorBody()?.string()
        val detail = runCatching { org.json.JSONObject(body ?: "{}").optString("detail") }.getOrNull()
        if (!detail.isNullOrBlank()) return detail
        return "El servidor respondió con un error (HTTP ${error.code()}). Intentá de nuevo."
    }
    return when (error) {
        is SocketTimeoutException -> "El servidor tardó demasiado en responder. Si estabas leyendo un ticket, tocá ‘Volver a leer la foto tomada’ para reintentar."
        is UnknownHostException ->
            "No se encuentra la dirección del servidor. Verificá Internet; si usás un enlace temporal, puede haber vencido. Necesitás una dirección vigente y actualizar la app. La foto tomada se conserva para reintentar."
        is ConnectException, is NoRouteToHostException ->
            "El servidor no está disponible. Verificá que la API y el enlace HTTPS estén activos. La foto tomada se conserva para reintentar."
        is java.io.IOException -> if (error.message == "HTTPS_REQUIRED")
            "El servidor necesita una dirección HTTPS válida antes de iniciar sesión desde el celular. HTTP no protege tus credenciales."
            else "Se interrumpió la comunicación con el servidor. Revisá la conexión y reintentá."
        else -> "No se pudo procesar la respuesta del servidor. Intentá de nuevo."
    }
}
