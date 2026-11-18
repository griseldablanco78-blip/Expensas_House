package com.expensahouse.app

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.expensahouse.app.data.ocr.DeviceReceiptOcr
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.ByteArrayOutputStream

@RunWith(AndroidJUnit4::class)
class DeviceReceiptOcrTest {
    @Test fun readsRealTextAtBothEndsAndPreservesCompleteImage() = runBlocking {
        val bitmap = Bitmap.createBitmap(1200,2000,Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(Color.WHITE)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color=Color.BLACK; textSize=52f }
        canvas.drawText("SUPERMERCADO PRUEBA",50f,100f,paint)
        canvas.drawText("LECHE 1500,00",50f,500f,paint)
        canvas.drawText("ARROZ 1200,00",50f,1000f,paint)
        canvas.drawText("TOTAL 2700,00",50f,1900f,paint)
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG,95,stream)
        bitmap.recycle()
        val result = DeviceReceiptOcr.read(stream.toByteArray())
        assertTrue(result.text.contains("SUPERMERCADO"))
        assertTrue(result.text.contains("LECHE"))
        assertTrue(result.text.contains("ARROZ"))
        assertTrue(result.text.contains("TOTAL"))
        assertTrue(result.jpeg.size <= 3_500_000)
        val restored = BitmapFactory.decodeByteArray(result.jpeg,0,result.jpeg.size)
        assertEquals(1200,restored.width)
        assertEquals(2000,restored.height)
        restored.recycle()
    }
}
