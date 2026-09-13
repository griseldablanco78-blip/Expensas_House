package com.expensahouse.app.data.local

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Update
import com.expensahouse.app.domain.model.*
import kotlinx.coroutines.flow.Flow

@Dao
interface ExpensaDao {
    // Stock
    @Query("SELECT * FROM stock_items")
    fun getAllStock(): Flow<List<StockItem>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertStock(item: StockItem)

    @Update
    suspend fun updateStock(item: StockItem)

    @Delete
    suspend fun deleteStock(item: StockItem)

    @Query("DELETE FROM stock_items")
    suspend fun clearStock()

    // Shopping
    @Query("SELECT * FROM shopping_items")
    fun getAllShopping(): Flow<List<ShoppingItem>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertShopping(item: ShoppingItem)

    @Update
    suspend fun updateShopping(item: ShoppingItem)

    @Query("DELETE FROM shopping_items WHERE id = :id")
    suspend fun deleteShoppingById(id: String)

    @Query("DELETE FROM shopping_items WHERE name = :name")
    suspend fun deleteShoppingByName(name: String)

    @Query("DELETE FROM shopping_items")
    suspend fun clearShopping()

    // Offers
    @Query("SELECT * FROM offers")
    fun getAllOffers(): Flow<List<Offer>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOffer(offer: Offer)

    @Query("DELETE FROM offers")
    suspend fun clearOffers()

    // Prefs
    @Query("SELECT * FROM user_prefs WHERE id = 0")
    fun getUserPrefs(): Flow<UserPrefs?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveUserPrefs(prefs: UserPrefs)
}

@Database(entities = [StockItem::class, ShoppingItem::class, Offer::class, UserPrefs::class], version = 3, exportSchema = false)
abstract class ExpensaDatabase : RoomDatabase() {
    abstract val dao: ExpensaDao
}
