package com.expensahouse.app.data.repository

import com.expensahouse.app.data.remote.*
import okhttp3.MultipartBody

interface ChatRepository {
    suspend fun chat(request: ChatRequest): ChatAnswer
}

class RemoteChatRepository(private val api: ExpensaApi) : ChatRepository {
    override suspend fun chat(request: ChatRequest): ChatAnswer = api.chat(request)
}
