package com.expensahouse.app.data.remote

import com.expensahouse.app.BuildConfig
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query
import retrofit2.http.Multipart
import retrofit2.http.Part
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit
import com.expensahouse.app.core.auth.*

interface ExpensaApi {
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): AccountResponse
    @POST("api/auth/register")
    suspend fun register(@Body request: RegisterRequest): AccountResponse
    @POST("api/auth/verify")
    suspend fun verifyEmail(@Body request: VerifyRequest): AccountResponse
    @POST("api/auth/resend-verification")
    suspend fun resendVerification(@Body request: EmailRequest): AccountResponse
    @POST("api/auth/forgot-password")
    suspend fun forgotPassword(@Body request: EmailRequest): AccountResponse
    @POST("api/auth/reset-password")
    suspend fun resetPassword(@Body request: VerifyRequest): AccountResponse
    @POST("api/auth/change-password")
    suspend fun changePassword(@Body request: ChangePasswordRequest): AccountResponse
    @POST("api/auth/logout")
    suspend fun logout(): AccountResponse
    @POST("api/auth/accept-invitation")
    suspend fun acceptInvitation(@Body request: InvitationRequest): AccountResponse
    @GET("api/offers/compare")
    suspend fun compare(@Query("q") query: String, @Query("sort") sort: String = "discount"): Comparison

    @POST("api/ai/chat")
    suspend fun chat(@Body request: ChatRequest): ChatAnswer

    @Multipart
    @POST("api/receipts/scan")
    suspend fun scanReceipt(@Part image: MultipartBody.Part): ReceiptDraft

    @POST("api/receipts/parse")
    suspend fun parseReceipt(@Body text: ReceiptText): ReceiptDraft

    @POST("api/receipts/confirm")
    suspend fun confirmReceipt(@Body receipt: ReceiptCommit): Map<String, Any>

    @GET("api/sync")
    suspend fun getSyncSnapshot(): SyncResponse

    @POST("api/sync")
    suspend fun syncSnapshot(@Body payload: AndroidSyncPayload): SyncResponse
}

object ExpensaApiClient {
    val service: ExpensaApi by lazy {
        Retrofit.Builder()
            .client(OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(60, TimeUnit.SECONDS)
                .addInterceptor { chain ->
                    val request = chain.request()
                    val localDebug = BuildConfig.DEBUG && request.url().host() in setOf("127.0.0.1", "localhost", "10.0.2.2")
                    if (!request.url().isHttps() && !localDebug) throw java.io.IOException("HTTPS_REQUIRED")
                    val builder = request.newBuilder()
                    AuthSession.token?.let { builder.header("Authorization", "Bearer $it") }
                    val response = chain.proceed(builder.build())
                    if (response.code() == 401 && !request.url().encodedPath().startsWith("/api/auth/")) AuthSession.clear()
                    response
                }.build())
            .baseUrl(BuildConfig.API_BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ExpensaApi::class.java)
    }
}
