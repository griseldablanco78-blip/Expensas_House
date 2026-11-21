package com.expensahouse.app

import androidx.compose.runtime.*
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.expensahouse.app.ui.features.auth.PasswordInputField
import org.junit.Rule
import org.junit.Test

class PasswordVisibilityTest {
    @get:Rule val compose = createComposeRule()
    @Test fun passwordIsMaskedUnlessUserRevealsAndCanHideAgain() {
        compose.setContent {
            var password by remember { mutableStateOf("") }
            PasswordInputField(password,{password=it},"Contraseña")
        }
        val field=compose.onNodeWithText("Contraseña")
        field.performTextInput("FraseFicticiaSoloParaQA")
        field.assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Password))
        compose.onNodeWithContentDescription("Mostrar contraseña").performClick()
        field.assert(SemanticsMatcher("No password transformation") { !it.config.contains(SemanticsProperties.Password) })
        compose.onNodeWithContentDescription("Ocultar contraseña").performClick()
        field.assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Password))
        compose.onNodeWithContentDescription("Mostrar contraseña").performClick()
        field.performTextClearance()
        compose.onNodeWithContentDescription("Mostrar contraseña").assertExists()
        field.assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Password))
    }
}
