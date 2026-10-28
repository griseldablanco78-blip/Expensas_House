"""Voice HTTP routes."""
from fastapi import APIRouter
import io
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter(tags=["voice"])


@router.post("/api/voice/transcribe")
async def api_voice_transcribe(audio: UploadFile = File(...)):
    """
    Endpoint de transcripción de voz a texto del lado del servidor.
    Complementa el Web Speech API del navegador cuando el usuario sube un clip de audio.
    """
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        audio_bytes = await audio.read()
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="es-AR")
            return {"status": "success", "text": text}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"No se pudo transcribir el audio: {str(e)}"}
        )
