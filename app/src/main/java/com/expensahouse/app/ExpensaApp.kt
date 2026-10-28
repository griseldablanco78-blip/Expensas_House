package com.expensahouse.app

import android.app.Application
import androidx.room.Room
import com.expensahouse.app.data.local.ExpensaDatabase

class ExpensaApp : Application() {
    private val databases = mutableMapOf<String, ExpensaDatabase>()
    val database: ExpensaDatabase
        @Synchronized get() {
            val id = requireNotNull(com.expensahouse.app.core.auth.AuthSession.user.value).id
            return databases.getOrPut(id) {
                Room.databaseBuilder(applicationContext, ExpensaDatabase::class.java,
                    "expensa_account_${id}.db").build()
            }
        }
}
