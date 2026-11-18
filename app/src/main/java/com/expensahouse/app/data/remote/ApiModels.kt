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
data class Comparison(
    val offers: List<ProductOffer> = emptyList(), val warning: String? = null,
    val product_name: String? = null, val cleaned_query: String? = null,
    val top_offer: ProductOffer? = null, val ai_analysis: ComparisonAnalysis? = null,
    val external_search_url: String? = null
)
data class BestPrice(val store: String = "", val price: Double = 0.0)
data class ComparisonAnalysis(val best_single: BestPrice? = null, val max_saving_percent: Double = 0.0,
    val verdict: String? = null, val stock_alert: String? = null)
data class ProductOffer(val product: String, val store: String, val promo_price: Double,
    val promo_text: String, val image_url: String? = null, val direct_link: String? = null,
    val conditions: String? = null, val source: String? = null,
    val id: String = "", val brand: String? = null, val saving_percent: Double = 0.0,
    val promo_type: String? = null, val size_confirmed: Boolean = true,
    val updated_at: String? = null, val unit: String? = null, val unit_price: Double? = null)
data class ReceiptText(val text: String)
data class ReceiptLine(val description: String, val quantity: Double, val unit_price: Double, val line_total: Double, val detail: String = "", val discount: Double = 0.0)
data class ReceiptDraft(val items: List<ReceiptLine>, val total: Double, val warnings: List<String>, val raw_text: String, val receipt_image: String? = null, val vat_amount: Double? = null, val vat_included: Boolean = true, val store: String? = null, val purchase_date: String? = null)
data class ReceiptCommit(val id: String, val store: String, val items: List<ReceiptLine>, val total: Double, val adjustment_note: String = "", val purchase_date: String? = null, val raw_text: String = "", val receipt_image: String = "", val vat_amount: Double? = null, val vat_included: Boolean = true)

// Separate read model: receipt metadata must not alter the offline Room schema.
data class ReceiptSummary(val id: String, val amount: Double, val store: String? = null,
    val note: String? = null, val purchase_date: String? = null, val timestamp: Long? = null,
    val items: List<ReceiptLine>? = null, val vat_amount: Double? = null, val vat_included: Boolean = true)
