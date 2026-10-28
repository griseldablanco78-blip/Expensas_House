package com.expensahouse.app.core.di

import com.expensahouse.app.data.remote.ExpensaApiClient
import com.expensahouse.app.data.repository.*

/** Application wiring. Feature UI depends on injectable repository interfaces. */
object AppContainer {
    val offersRepository: OffersRepository by lazy { RemoteOffersRepository(ExpensaApiClient.service) }
    val chatRepository: ChatRepository by lazy { RemoteChatRepository(ExpensaApiClient.service) }
    val receiptsRepository: ReceiptsRepository by lazy { RemoteReceiptsRepository(ExpensaApiClient.service) }
}
