import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pymongo import MongoClient

app = FastAPI(title="Luminex / Widman iOS API")

# Habilitar CORS completo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://deymejiamejia_db_user:s8dQN2nKX4XksG2t@damian.c8zoazk.mongodb.net/LuminexDB?retryWrites=true&w=majority&appName=Damian"
)

client = MongoClient(MONGO_URI)
db = client['LuminexDB']
keys_col = db['keys']

@app.get("/")
def inicio():
    return {"status": "ok", "mensaje": "API activa"}

@app.get("/validar-key")
def validar_key(key: str = Query(...)):
    try:
        key_limpia = key.strip()
        key_doc = keys_col.find_one({"key": key_limpia})

        if not key_doc:
            return JSONResponse(status_code=200, content={"valida": False, "error": "La Key ingresada no existe."})

        if key_doc.get("usada", False):
            return JSONResponse(status_code=200, content={"valida": False, "error": "Esta Key ya fue utilizada."})

        return JSONResponse(status_code=200, content={"valida": True, "mensaje": "Key correcta"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"valida": False, "error": f"Error en servidor: {str(e)}"})

@app.post("/modificar-archivo")
async def modificar_archivo(key: str = Form(...), file: UploadFile = File(...)):
    key_doc = keys_col.find_one({"key": key.strip()})
    if not key_doc or key_doc.get("usada", False):
        raise HTTPException(status_code=403, detail="Key no autorizada o expirada.")

    input_filename = f"temp_{file.filename}"
    output_filename = f"modificado_{file.filename}"

    try:
        with open(input_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        shutil.copy(input_filename, output_filename)

        return FileResponse(
            path=output_filename,
            filename=f"modificado_{file.filename}",
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if os.path.exists(input_filename):
            os.remove(input_filename)
