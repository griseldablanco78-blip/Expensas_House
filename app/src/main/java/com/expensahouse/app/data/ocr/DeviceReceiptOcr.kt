package com.expensahouse.app.data.ocr

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import androidx.exifinterface.media.ExifInterface
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.coroutines.suspendCoroutine
import kotlin.math.roundToInt

/** Lee la foto completa en el dispositivo y prepara una copia privada sin EXIF. */
object DeviceReceiptOcr {
    data class Result(val text: String, val jpeg: ByteArray)

    suspend fun read(bytes: ByteArray): Result = withContext(Dispatchers.Default) {
        require(bytes.isNotEmpty() && bytes.size <= 10 * 1024 * 1024) { "La foto debe pesar menos de 10 MB." }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        require(bounds.outWidth > 0 && bounds.outHeight > 0) { "La foto no es válida." }
        require(bounds.outWidth.toLong() * bounds.outHeight <= 25_000_000L) { "La foto supera 25 megapíxeles." }
        var sample = 1
        while (bounds.outWidth / sample > 2400 || bounds.outHeight / sample > 6000) sample *= 2
        var bitmap = requireNotNull(BitmapFactory.decodeByteArray(bytes, 0, bytes.size,
            BitmapFactory.Options().apply { inSampleSize = sample })) { "No se pudo abrir la foto." }
        val orientation = ExifInterface(ByteArrayInputStream(bytes)).getAttributeInt(
            ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
        val matrix = Matrix().apply {
            when (orientation) {
                ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> setScale(-1f,1f)
                ExifInterface.ORIENTATION_ROTATE_180 -> setRotate(180f)
                ExifInterface.ORIENTATION_FLIP_VERTICAL -> setScale(1f,-1f)
                ExifInterface.ORIENTATION_TRANSPOSE -> { setRotate(90f); postScale(-1f,1f) }
                ExifInterface.ORIENTATION_ROTATE_90 -> setRotate(90f)
                ExifInterface.ORIENTATION_TRANSVERSE -> { setRotate(-90f); postScale(-1f,1f) }
                ExifInterface.ORIENTATION_ROTATE_270 -> setRotate(-90f)
            }
        }
        val oriented = Bitmap.createBitmap(bitmap,0,0,bitmap.width,bitmap.height,matrix,true)
        if (oriented !== bitmap) { bitmap.recycle(); bitmap = oriented }
        val factor = minOf(1f,2000f/bitmap.width,6000f/bitmap.height)
        if (factor < 1f) {
            val resized = Bitmap.createScaledBitmap(bitmap,(bitmap.width*factor).roundToInt().coerceAtLeast(1),
                (bitmap.height*factor).roundToInt().coerceAtLeast(1),true)
            bitmap.recycle(); bitmap = resized
        }
        val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        try {
            val text = suspendCoroutine<String> { continuation ->
                recognizer.process(InputImage.fromBitmap(bitmap,0))
                    .addOnSuccessListener { continuation.resume(it.text) }
                    .addOnFailureListener { continuation.resumeWithException(it) }
            }.trim()
            require(text.isNotBlank()) { "No se reconoció texto. Probá una foto completa y nítida." }
            val output = ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG,88,output)
            val jpeg = output.toByteArray()
            require(jpeg.size <= 3_500_000) { "La imagen preparada supera 3,5 MB." }
            Result(text,jpeg)
        } finally { recognizer.close(); bitmap.recycle() }
    }
}
