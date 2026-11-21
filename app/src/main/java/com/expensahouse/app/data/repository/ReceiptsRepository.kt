package com.expensahouse.app.data.repository

import com.expensahouse.app.data.remote.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.MediaType
import okio.Buffer
import com.expensahouse.app.data.ocr.DeviceReceiptOcr

interface ReceiptsRepository {
    suspend fun delete(id: String) { error("Eliminación no disponible") }
    suspend fun image(id: String): ByteArray = error("Imagen no disponible")
    suspend fun history(): List<ReceiptSummary> = emptyList()
    suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft
    suspend fun parseReceipt(text: ReceiptText): ReceiptDraft
    suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any>
}

class RemoteReceiptsRepository(private val api: ExpensaApi) : ReceiptsRepository {
    override suspend fun delete(id: String) { api.deleteReceipt(id) }
    override suspend fun image(id: String): ByteArray = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        api.receiptImage(id).use { it.bytes() }
    }
    override suspend fun history(): List<ReceiptSummary> = api.receiptHistory()
    override suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft {
        val buffer = Buffer()
        image.body().writeTo(buffer)
        val result = DeviceReceiptOcr.read(buffer.readByteArray())
        return api.draftReceipt(
            RequestBody.create(MediaType.parse("text/plain; charset=utf-8"), result.text),
            MultipartBody.Part.createFormData("image", "ticket.jpg",
                RequestBody.create(MediaType.parse("image/jpeg"),result.jpeg))
        )
    }
    override suspend fun parseReceipt(text: ReceiptText): ReceiptDraft = api.parseReceipt(text)
    override suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any> = api.confirmReceipt(receipt)
}
