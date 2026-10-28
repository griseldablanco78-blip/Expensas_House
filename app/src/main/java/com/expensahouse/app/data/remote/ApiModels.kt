package com.expensahouse.app.data.remote

import com.expensahouse.app.domain.model.*
import com.google.gson.annotations.SerializedName

data class AndroidSyncPayload(
    val stock: List<StockItem>,
    val shopping: List<ShoppingItem>,
    val expenses: List<Expense>,
    @SerializedName("user_prefs") val userPrefs: UserPrefs,
    val offers: List<Offer>,
    val baseline: SyncSnapshot? = null
)

data class SyncSnapshot(
    val stock: List<StockItem> = emptyList(),
    val shopping: List<ShoppingItem> = emptyList(),
    val expenses: List<Expense> = emptyList(),
    @SerializedName("user_prefs") val userPrefs: UserPrefs = UserPrefs(),
    val offers: List<Offer> = emptyList()
)

data class SyncResponse(
    val status: String,
    val data: SyncSnapshot,
    val message: String? = null
)

data class ChatRequest(val message: String, val context: String? = null)
data class ChatAnswer(val answer: String, val action: String? = null, val context: String? = null, val comparison: Comparison? = null)
data class Comparison(val offers: List<ProductOffer> = emptyList(), val warning: String? = null)
data class ProductOffer(val product: String, val store: String, val promo_price: Double,
    val promo_text: String, val image_url: String? = null, val direct_link: String? = null,
    val conditions: String? = null, val source: String? = null)
data class ReceiptText(val text: String)
data class ReceiptLine(val description: String, val quantity: Double, val unit_price: Double, val line_total: Double)
data class ReceiptDraft(val items: List<ReceiptLine>, val total: Double, val warnings: List<String>, val raw_text: String, val receipt_image: String? = null)
data class ReceiptCommit(val id: String, val store: String, val items: List<ReceiptLine>, val total: Double, val adjustment_note: String = "", val purchase_date: String? = null, val raw_text: String = "", val receipt_image: String = "")
