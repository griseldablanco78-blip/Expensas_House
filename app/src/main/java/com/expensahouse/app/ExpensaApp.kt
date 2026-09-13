package com.expensahouse.app

import android.app.Application
import androidx.room.Room
import com.expensahouse.app.data.local.ExpensaDatabase

class ExpensaApp : Application() {
    lateinit var database: ExpensaDatabase
        private set

    override fun onCreate() {
        super.onCreate()
        database = Room.databaseBuilder(
            applicationContext,
            ExpensaDatabase::class.java,
            "expensa_db"
        ).fallbackToDestructiveMigration().build()
    }
}
