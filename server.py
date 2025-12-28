from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from jose import jwt, JWTError
import qrcode
import io
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
SECRET_KEY = os.environ.get('JWT_SECRET', 'super-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Create the main app
app = FastAPI(title="QR Access Control - U.E. Rómulo Gallegos")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class AdminCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nombre: str
    apellido: str
    email: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse

class PersonalBase(BaseModel):
    nombre: str
    apellido: str
    cedula: str
    rol: str  # Director, Docente, Administrativo, Obrero

class PersonalCreate(PersonalBase):
    pass

class PersonalResponse(PersonalBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    qr_code: str
    created_at: str

class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    cedula: Optional[str] = None
    rol: Optional[str] = None

class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    cedula: str
    ano: int  # 1, 2, 3, 4, 5
    seccion: str  # A, B, C, D

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteResponse(EstudianteBase):
    model_config = ConfigDict(extra="ignore")
    id: str
    qr_code: str
    created_at: str

class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    cedula: Optional[str] = None
    ano: Optional[int] = None
    seccion: Optional[str] = None

class AsistenciaCreate(BaseModel):
    cedula: str

class AsistenciaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    cedula: str
    nombre: str
    apellido: str
    tipo: str  # personal o estudiante
    rol_o_ano: str
    timestamp: str

# ==================== HELPER FUNCTIONS ====================

def generate_qr_code(data: str) -> str:
    """Generate QR code as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        if admin_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        admin = await db.admins.find_one({"id": admin_id}, {"_id": 0})
        if admin is None:
            raise HTTPException(status_code=401, detail="Admin no encontrado")
        return admin
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register_admin(admin_data: AdminCreate):
    # Check if email exists
    existing = await db.admins.find_one({"email": admin_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    admin_id = str(uuid.uuid4())
    admin_doc = {
        "id": admin_id,
        "nombre": admin_data.nombre,
        "apellido": admin_data.apellido,
        "email": admin_data.email,
        "password": hash_password(admin_data.password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admins.insert_one(admin_doc)
    
    token = create_access_token({"sub": admin_id})
    admin_response = AdminResponse(
        id=admin_id,
        nombre=admin_data.nombre,
        apellido=admin_data.apellido,
        email=admin_data.email,
        created_at=admin_doc["created_at"]
    )
    
    return TokenResponse(access_token=token, admin=admin_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_admin(login_data: AdminLogin):
    admin = await db.admins.find_one({"email": login_data.email}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    if not verify_password(login_data.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    token = create_access_token({"sub": admin["id"]})
    admin_response = AdminResponse(
        id=admin["id"],
        nombre=admin["nombre"],
        apellido=admin["apellido"],
        email=admin["email"],
        created_at=admin["created_at"]
    )
    
    return TokenResponse(access_token=token, admin=admin_response)

@api_router.get("/auth/me", response_model=AdminResponse)
async def get_me(admin = Depends(get_current_admin)):
    return AdminResponse(
        id=admin["id"],
        nombre=admin["nombre"],
        apellido=admin["apellido"],
        email=admin["email"],
        created_at=admin["created_at"]
    )

# ==================== PERSONAL ROUTES ====================

@api_router.post("/personal", response_model=PersonalResponse)
async def create_personal(personal: PersonalCreate, admin = Depends(get_current_admin)):
    # Check if cedula exists
    existing = await db.personal.find_one({"cedula": personal.cedula})
    if existing:
        raise HTTPException(status_code=400, detail="La cédula ya está registrada")
    
    personal_id = str(uuid.uuid4())
    qr_code = generate_qr_code(personal.cedula)
    
    doc = {
        "id": personal_id,
        "nombre": personal.nombre,
        "apellido": personal.apellido,
        "cedula": personal.cedula,
        "rol": personal.rol,
        "qr_code": qr_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.personal.insert_one(doc)
    
    return PersonalResponse(**{k: v for k, v in doc.items() if k != "_id"})

@api_router.get("/personal", response_model=List[PersonalResponse])
async def get_all_personal(admin = Depends(get_current_admin)):
    personal_list = await db.personal.find({}, {"_id": 0}).to_list(1000)
    return personal_list

@api_router.get("/personal/{personal_id}", response_model=PersonalResponse)
async def get_personal(personal_id: str, admin = Depends(get_current_admin)):
    personal = await db.personal.find_one({"id": personal_id}, {"_id": 0})
    if not personal:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return personal

@api_router.put("/personal/{personal_id}", response_model=PersonalResponse)
async def update_personal(personal_id: str, update_data: PersonalUpdate, admin = Depends(get_current_admin)):
    personal = await db.personal.find_one({"id": personal_id})
    if not personal:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # If cedula changed, regenerate QR and check uniqueness
    if "cedula" in update_dict and update_dict["cedula"] != personal["cedula"]:
        existing = await db.personal.find_one({"cedula": update_dict["cedula"], "id": {"$ne": personal_id}})
        if existing:
            raise HTTPException(status_code=400, detail="La cédula ya está registrada")
        update_dict["qr_code"] = generate_qr_code(update_dict["cedula"])
    
    if update_dict:
        await db.personal.update_one({"id": personal_id}, {"$set": update_dict})
    
    updated = await db.personal.find_one({"id": personal_id}, {"_id": 0})
    return updated

@api_router.delete("/personal/{personal_id}")
async def delete_personal(personal_id: str, admin = Depends(get_current_admin)):
    result = await db.personal.delete_one({"id": personal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    return {"message": "Personal eliminado exitosamente"}

# ==================== ESTUDIANTES ROUTES ====================

@api_router.post("/estudiantes", response_model=EstudianteResponse)
async def create_estudiante(estudiante: EstudianteCreate, admin = Depends(get_current_admin)):
    existing = await db.estudiantes.find_one({"cedula": estudiante.cedula})
    if existing:
        raise HTTPException(status_code=400, detail="La cédula ya está registrada")
    
    estudiante_id = str(uuid.uuid4())
    qr_code = generate_qr_code(estudiante.cedula)
    
    doc = {
        "id": estudiante_id,
        "nombre": estudiante.nombre,
        "apellido": estudiante.apellido,
        "cedula": estudiante.cedula,
        "ano": estudiante.ano,
        "seccion": estudiante.seccion,
        "qr_code": qr_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.estudiantes.insert_one(doc)
    
    return EstudianteResponse(**{k: v for k, v in doc.items() if k != "_id"})

@api_router.get("/estudiantes", response_model=List[EstudianteResponse])
async def get_all_estudiantes(admin = Depends(get_current_admin)):
    estudiantes_list = await db.estudiantes.find({}, {"_id": 0}).to_list(1000)
    return estudiantes_list

@api_router.get("/estudiantes/{estudiante_id}", response_model=EstudianteResponse)
async def get_estudiante(estudiante_id: str, admin = Depends(get_current_admin)):
    estudiante = await db.estudiantes.find_one({"id": estudiante_id}, {"_id": 0})
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante

@api_router.put("/estudiantes/{estudiante_id}", response_model=EstudianteResponse)
async def update_estudiante(estudiante_id: str, update_data: EstudianteUpdate, admin = Depends(get_current_admin)):
    estudiante = await db.estudiantes.find_one({"id": estudiante_id})
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if "cedula" in update_dict and update_dict["cedula"] != estudiante["cedula"]:
        existing = await db.estudiantes.find_one({"cedula": update_dict["cedula"], "id": {"$ne": estudiante_id}})
        if existing:
            raise HTTPException(status_code=400, detail="La cédula ya está registrada")
        update_dict["qr_code"] = generate_qr_code(update_dict["cedula"])
    
    if update_dict:
        await db.estudiantes.update_one({"id": estudiante_id}, {"$set": update_dict})
    
    updated = await db.estudiantes.find_one({"id": estudiante_id}, {"_id": 0})
    return updated

@api_router.delete("/estudiantes/{estudiante_id}")
async def delete_estudiante(estudiante_id: str, admin = Depends(get_current_admin)):
    result = await db.estudiantes.delete_one({"id": estudiante_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"message": "Estudiante eliminado exitosamente"}

# ==================== ASISTENCIA ROUTES ====================

@api_router.post("/asistencia", response_model=AsistenciaResponse)
async def registrar_asistencia(asistencia: AsistenciaCreate):
    cedula = asistencia.cedula
    
    # Search in personal first
    persona = await db.personal.find_one({"cedula": cedula}, {"_id": 0})
    tipo = "personal"
    rol_o_ano = ""
    
    if persona:
        rol_o_ano = persona["rol"]
    else:
        # Search in estudiantes
        persona = await db.estudiantes.find_one({"cedula": cedula}, {"_id": 0})
        tipo = "estudiante"
        if persona:
            rol_o_ano = f"{persona['ano']}° {persona['seccion']}"
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada con esta cédula")
    
    asistencia_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "id": asistencia_id,
        "cedula": cedula,
        "nombre": persona["nombre"],
        "apellido": persona["apellido"],
        "tipo": tipo,
        "rol_o_ano": rol_o_ano,
        "timestamp": timestamp
    }
    
    await db.asistencias.insert_one(doc)
    
    return AsistenciaResponse(**{k: v for k, v in doc.items() if k != "_id"})

@api_router.get("/asistencias", response_model=List[AsistenciaResponse])
async def get_asistencias(
    fecha: Optional[str] = None,
    admin = Depends(get_current_admin)
):
    query = {}
    if fecha:
        # Filter by date (YYYY-MM-DD)
        query["timestamp"] = {"$regex": f"^{fecha}"}
    
    asistencias = await db.asistencias.find(query, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return asistencias

@api_router.get("/asistencias/hoy", response_model=List[AsistenciaResponse])
async def get_asistencias_hoy():
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    asistencias = await db.asistencias.find(
        {"timestamp": {"$regex": f"^{hoy}"}}, 
        {"_id": 0}
    ).sort("timestamp", -1).to_list(1000)
    return asistencias

# ==================== STATS ROUTES ====================

@api_router.get("/stats")
async def get_stats(admin = Depends(get_current_admin)):
    total_personal = await db.personal.count_documents({})
    total_estudiantes = await db.estudiantes.count_documents({})
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    asistencias_hoy = await db.asistencias.count_documents({"timestamp": {"$regex": f"^{hoy}"}})
    
    return {
        "total_personal": total_personal,
        "total_estudiantes": total_estudiantes,
        "asistencias_hoy": asistencias_hoy
    }

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "API Control de Acceso QR - U.E. Rómulo Gallegos"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
