package com.expensahouse.app.data.remote

import com.expensahouse.app.domain.model.Offer
import retrofit2.http.GET
import retrofit2.http.Query

// Nota: En un caso real, aquí iría la URL de la API del supermercado (Coto, Carrefour, etc.)
// Como no hay una API pública gratuita universal, simularemos los resultados.

interface SupermarketApi {
    @GET("offers")
    suspend fun getOffers(@Query("q") query: String): List<RemoteOffer>
}

data class RemoteOffer(
    val store: String,
    val name: String,
    val brand: String,
    val price: String,
    val discount: String
)

fun RemoteOffer.toOffer() = Offer(
    store = store,
    product = name,
    brand = brand,
    price = price,
    saving = discount,
    isExternal = true
)
