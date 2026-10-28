package com.expensahouse.app.core.auth

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AccountUser(val id: String, val email: String, val role: String?)
data class AccountResponse(val user: AccountUser?, val access_token: String? = null, val message: String? = null)
data class LoginRequest(val email: String, val password: String, val client: String = "android")
data class RegisterRequest(val email: String, val password: String)
data class VerifyRequest(val token: String, val password: String)
data class EmailRequest(val email: String)
data class ChangePasswordRequest(val current_password: String, val new_password: String)
data class InvitationRequest(val token: String)

/** Tokens stay in memory; restarting the app requires signing in again. */
object AuthSession {
    @Volatile var token: String? = null
        private set
    private val account = MutableStateFlow<AccountUser?>(null)
    val user = account.asStateFlow()
    val canEdit: Boolean get() = account.value?.role in setOf("admin", "full_editor")
    fun start(response: AccountResponse) {
        token = requireNotNull(response.access_token)
        account.value = requireNotNull(response.user)
    }
    fun clear() { token = null; account.value = null }
    fun updateUser(user: AccountUser) { account.value = user }
}
