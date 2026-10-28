package com.expensahouse.app.data.repository

import com.expensahouse.app.data.remote.*
import okhttp3.MultipartBody

interface OffersRepository {
    suspend fun compare(query: String, sort: String): Comparison
}

class RemoteOffersRepository(private val api: ExpensaApi) : OffersRepository {
    override suspend fun compare(query: String, sort: String): Comparison = api.compare(query, sort)
}
