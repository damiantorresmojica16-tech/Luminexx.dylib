import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pymongo import MongoClient

app = FastAPI(title="Luminex / Widman iOS API")

# 1. Configurar CORS para permitir peticiones desde Netlify / Navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite conexiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Conexión a MongoDB Atlas
# Obtiene la variable de entorno MONGO_URI de Render (o usa la URI directa de respaldo)
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://deymejiamejia_db_user:s8dQN2nKX4XksG2t@damian.c8zoazk.mongodb.net/LuminexDB?retryWrites=true&w=majority&appName=Damian"
)

client = MongoClient(MONGO_URI)
db = client['LuminexDB']
keys_col = db['keys']  # Colección donde están guardadas las keys generadas por el bot


@app.get("/")
def inicio():
    """Ruta principal para comprobar que la API está activa."""
    return {"status": "ok", "mensaje": "API de Widman iOS activa y lista"}


@app.get("/validar-key")
def validar_key(key: str):
    """
    Endpoint para consultar en MongoDB si la Key existe y está activa.
    """
    if not key:
        return {"valida": False, "error": "Debes ingresar una key."}

    # Buscar la key en la colección de MongoDB
    key_doc = keys_col.find_one({"key": key.strip()})

    if not key_doc:
        return {"valida": False, "error": "La Key ingresada no existe."}

    # Verificar si está inactiva o ya usada (según los campos que guarde tu bot)
    if key_doc.get("usada", False):
        return {"valida": False, "error": "Esta Key ya fue utilizada o ha expirado."}

    return {"valida": True, "mensaje": "Key correcta"}


@app.post("/modificar-archivo")
async def modificar_archivo(key: str = Form(...), file: UploadFile = File(...)):
    """
    Endpoint para recibir el archivo (.dylib / .deb / etc.),
    validar la key, aplicar las modificaciones/hologramas y devolverlo.
    """
    # 1. Validar la key antes de procesar el archivo
    key_doc = keys_col.find_one({"key": key.strip()})
    if not key_doc:
        raise HTTPException(status_code=403, detail="Key no autorizada o inexistente.")

    if key_doc.get("usada", False):
        raise HTTPException(status_code=403, detail="Key expirada o ya utilizada.")

    # Nombres de archivos temporales para el procesamiento
    input_filename = f"temp_{file.filename}"
    output_filename = f"modificado_{file.filename}"

    try:
        # 2. Guardar el archivo subido en el servidor
        with open(input_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # =========================================================================
        # AQUÍ OCURRE LA MODIFICACIÓN DE TU ARCHIVO (HOLOGRAMAS / SHADERS / ETC.)
        # =========================================================================
        # Puedes invocar tu script de modificación, reemplazar binarios/bytes,
        # o ejecutar un comando en el sistema.
        # 
        # Por ahora, copia el archivo para simular el procesamiento:
        shutil.copy(input_filename, output_filename)
        # =========================================================================

        # 3. Retornar el archivo procesado al cliente para descarga automática
        return FileResponse(
            path=output_filename,
            filename=f"modificado_{file.filename}",
            media_type='application/octet-stream'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

    finally:
        # Limpiar archivos temporales para no llenar el almacenamiento de Render
        if os.path.exists(input_filename):
            os.remove(input_filename)
