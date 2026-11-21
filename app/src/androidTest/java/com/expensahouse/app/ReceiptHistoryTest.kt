package com.expensahouse.app

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.expensahouse.app.data.remote.*
import com.expensahouse.app.data.repository.ReceiptsRepository
import com.expensahouse.app.ui.features.receipts.*
import okhttp3.MultipartBody
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class ReceiptHistoryTest {
    @get:Rule val compose = createComposeRule()
    @Test fun loadButtonOpensScannerActionAndHistoryFiltersPurchaseDate() {
        var scan = 0
        var manual = 0
        val repository = object : ReceiptsRepository {
            override suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft = error("Read-only history")
            override suspend fun parseReceipt(text: ReceiptText): ReceiptDraft = error("Read-only history")
            override suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any> = error("Read-only history")
            override suspend fun history() = listOf(
                ReceiptSummary("old",1200.0,"Super QA",purchase_date="2026-10-01",items=listOf(ReceiptLine("ARROZ ANTIGUO QA",1.0,1200.0,1200.0))),
                ReceiptSummary("new",1500.0,"Super QA",purchase_date="2026-11-01",items=listOf(ReceiptLine("ARROZ NUEVO QA",1.0,1500.0,1500.0)))
            )
        }
        compose.setContent { Column(Modifier.verticalScroll(rememberScrollState())) {
            ReceiptActions({ scan++ }, { manual++ })
            ConnectedReceiptHistory(repository=repository)
        } }
        compose.onNodeWithText("Cargar ticket · foto o galería").performClick()
        compose.runOnIdle { assertEquals(1,scan); assertEquals(0,manual) }
        compose.waitUntil(5000) { compose.onAllNodesWithText("Fecha de compra: 2026-10-01").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("ARROZ ANTIGUO QA").assertDoesNotExist()
        compose.onNodeWithText("Elegir fecha del resumen").performScrollTo().performClick()
        compose.onNodeWithText("2026-10-01").performClick()
        compose.onNodeWithText("Fecha de compra: 2026-10-01").performScrollTo().performClick()
        compose.onNodeWithText("ARROZ ANTIGUO QA").assertExists()
        compose.onNodeWithText("ARROZ NUEVO QA").assertDoesNotExist()
        compose.onNodeWithText("Cerrar detalle").performClick()
        compose.onNodeWithText("ARROZ ANTIGUO QA").assertDoesNotExist()
    }
}
