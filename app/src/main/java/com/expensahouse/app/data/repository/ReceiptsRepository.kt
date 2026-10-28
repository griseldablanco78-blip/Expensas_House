package com.expensahouse.app.data.repository

import com.expensahouse.app.data.remote.*
import okhttp3.MultipartBody

interface ReceiptsRepository {
    suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft
    suspend fun parseReceipt(text: ReceiptText): ReceiptDraft
    suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any>
}

class RemoteReceiptsRepository(private val api: ExpensaApi) : ReceiptsRepository {
    override suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft = api.scanReceipt(image)
    override suspend fun parseReceipt(text: ReceiptText): ReceiptDraft = api.parseReceipt(text)
    override suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any> = api.confirmReceipt(receipt)
}
