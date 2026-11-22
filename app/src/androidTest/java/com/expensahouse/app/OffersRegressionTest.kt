package com.expensahouse.app

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Column
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.expensahouse.app.data.remote.*
import com.expensahouse.app.data.repository.OffersRepository
import com.expensahouse.app.ui.features.offers.ConnectedOfferSearch
import org.junit.Rule
import org.junit.Test

class OffersRegressionTest {
    @get:Rule val compose = createComposeRule()

    @Test fun comparisonShowsCompactCardsLoyaltyDetailsAndOffersBeyondTen() {
        val repository = object : OffersRepository {
            override suspend fun compare(query: String, sort: String) = Comparison(
                offers = (1..11).map { ProductOffer("Arroz QA $it", "Super QA", 1200.0, "Oferta QA", id="$it", brand="Marca QA", size_confirmed=false, loyalty_program="Club Día", loyalty_notice="Beneficios personales no calculados") },
                cleaned_query="arroz", ai_analysis=ComparisonAnalysis(verdict="Comparación QA", stock_alert="En casa: 2 cerradas")
            )
        }
        compose.setContent { Column(Modifier.verticalScroll(rememberScrollState())) { ConnectedOfferSearch("arroz", repository) } }
        compose.waitUntil(5000) { compose.onAllNodesWithText("11 ofertas · de menor a mayor precio").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("11 ofertas · de menor a mayor precio").assertExists()
        compose.onNodeWithText("Comparación QA").assertDoesNotExist()
        compose.onAllNodesWithText("Ver detalle").onFirst().performScrollTo().performClick()
        compose.onNodeWithText("Beneficios personales no calculados").assertExists()
        compose.onNodeWithText("Presentación sin confirmar").assertExists()
        compose.onNodeWithText("Arroz QA 11").assertDoesNotExist()
        compose.onNodeWithText("Ver más ofertas (10 de 11)").performScrollTo().performClick()
        compose.onNodeWithText("Arroz QA 11").performScrollTo().assertIsDisplayed()
    }
}
