package com.expensahouse.app.domain.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.UUID

@Entity(tableName = "stock_items")
data class StockItem(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val name: String,
    val brand: String = "Genérica",
    val category: String,
    val stockQuantity: Int,
    val inUseCount: Int = 0,
    val unit: String = "unidad"
)

@Entity(tableName = "shopping_items")
data class ShoppingItem(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val name: String,
    val brand: String = "Genérica",
    val category: String,
    val detail: String,
    val quantity: Int = 1,
    val suggestedStore: String? = null,
    val checked: Boolean = false
)

@Entity(tableName = "offers")
data class Offer(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val store: String,
    val product: String,
    val brand: String,
    val price: String,
    val saving: String,
    val isExternal: Boolean = false
)

@Entity(tableName = "user_prefs")
data class UserPrefs(
    @PrimaryKey val id: Int = 0,
    val monthlyBudget: Double = 0.0,
    val totalSpent: Double = 0.0 // Mantenemos para compatibilidad rápida
)

@Entity(tableName = "expenses")
data class Expense(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val category: String,
    val amount: Double,
    val timestamp: Long = System.currentTimeMillis()
)
