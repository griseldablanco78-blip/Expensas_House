package com.expensahouse.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.expensahouse.app.data.remote.*
import com.expensahouse.app.data.repository.ReceiptsRepository
import com.expensahouse.app.ui.features.receipts.ConnectedReceiptDialog
import okhttp3.MultipartBody
import org.junit.Rule
import org.junit.Test
import java.net.UnknownHostException

class ReceiptRegressionTest {
    @get:Rule val compose = createComposeRule()

    @Test fun offlineReadShowsActionableErrorAndCanRetry() {
        val repository = object : ReceiptsRepository {
            var offline = true
            override suspend fun scanReceipt(image: MultipartBody.Part): ReceiptDraft = throw AssertionError("Camera not used in this test")
            override suspend fun parseReceipt(text: ReceiptText): ReceiptDraft {
                if (offline) throw UnknownHostException("temporary.invalid")
                return ReceiptDraft(listOf(ReceiptLine("LECHE QA", 1.0, 1500.0, 1500.0)),1500.0,emptyList(),"LECHE QA 1500,00")
            }
            override suspend fun confirmReceipt(receipt: ReceiptCommit): Map<String, Any> = throw AssertionError("An unconfirmed read must not register a purchase")
        }
        compose.setContent { ConnectedReceiptDialog({}, {}, repository) }
        compose.onNodeWithText("Texto del ticket").performScrollTo().performTextInput("LECHE QA 1500,00")
        compose.onNodeWithText("Interpretar texto").performScrollTo().performClick()
        compose.onNodeWithText("No se encuentra la dirección del servidor", substring=true).assertExists()
        compose.runOnIdle { repository.offline = false }
        compose.onNodeWithText("Interpretar texto").performScrollTo().performClick()
        compose.onNodeWithText("LECHE QA", substring=false).assertExists()
    }
}
