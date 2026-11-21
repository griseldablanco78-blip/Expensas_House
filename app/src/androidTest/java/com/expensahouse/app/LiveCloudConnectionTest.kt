package com.expensahouse.app

import androidx.test.core.app.ApplicationProvider
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.expensahouse.app.core.auth.AuthSession
import com.expensahouse.app.core.auth.LoginRequest
import com.expensahouse.app.data.remote.ExpensaApiClient
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/** Solo lectura y sesión temporal. Requiere activación explícita en el teléfono migrado. */
@RunWith(AndroidJUnit4::class)
class LiveCloudConnectionTest {
    @Test fun androidSignsInAndMatchesMigratedRoomRecords() = runBlocking {
        assumeTrue(InstrumentationRegistry.getArguments().getString("liveCloud") == "true")
        assertEquals("https://expensas-house-griselda-blanco.vercel.app/",BuildConfig.API_BASE_URL)
        val api = ExpensaApiClient.service
        val arguments = InstrumentationRegistry.getArguments()
        val username = arguments.getString("liveUser").orEmpty()
        val password = arguments.getString("livePassword").orEmpty()
        assumeTrue("Configurar credenciales explícitas de prueba", username.isNotBlank() && password.isNotBlank())
        AuthSession.start(api.login(LoginRequest(username,password)))
        try {
            val context = ApplicationProvider.getApplicationContext<ExpensaApp>()
            val local = context.database.dao.getStockSnapshot()
            val remote = api.getSyncSnapshot().data.stock
            assertTrue(local.isNotEmpty())
            assertEquals(local.map { it.id }.toSet(),remote.map { it.id }.toSet())
        } finally {
            try { api.logout() } finally { AuthSession.clear() }
        }
    }
}
