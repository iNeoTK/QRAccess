# PRD - Sistema de Control de Acceso QR
## U.E. Rómulo Gallegos - Mérida, Venezuela

### Fecha de Creación: 2025-12-28

---

## 1. Problema Original

Desarrollar una aplicación web para el control de acceso mediante código QR para la institución educativa U.E. Rómulo Gallegos. La aplicación permite registrar asistencias escaneando códigos QR generados automáticamente al registrar personal y estudiantes.

---

## 2. Usuarios Objetivo

- **Administradores**: Personal autorizado que gestiona el registro de personal y estudiantes
- **Personal**: Director, Docentes, Administrativos, Obreros
- **Estudiantes**: Alumnos de 1° a 5° año, secciones A, B, C, D

---

## 3. Requisitos Funcionales (Implementados ✅)

### 3.1 Escáner QR (Página Principal)
- ✅ Escáner de códigos QR usando cámara del dispositivo
- ✅ Búsqueda manual por cédula
- ✅ Visualización de registros recientes del día
- ✅ Reloj en tiempo real
- ✅ Logo institucional

### 3.2 Autenticación
- ✅ Login con email y contraseña
- ✅ Registro de nuevos administradores
- ✅ JWT para sesiones seguras (24h)

### 3.3 Gestión de Personal
- ✅ CRUD completo (crear, listar, editar, eliminar)
- ✅ Campos: nombre, apellido, cédula, rol
- ✅ Roles: Director, Docente, Administrativo, Obrero
- ✅ Generación automática de QR con cédula
- ✅ Descarga de código QR en PNG

### 3.4 Gestión de Estudiantes
- ✅ CRUD completo
- ✅ Campos: nombre, apellido, cédula, año, sección
- ✅ Años: 1, 2, 3, 4, 5
- ✅ Secciones: A, B, C, D
- ✅ Filtros por año y sección
- ✅ Generación automática de QR

### 3.5 Historial de Asistencias
- ✅ Listado de asistencias por fecha
- ✅ Calendario para selección de fecha
- ✅ Estadísticas del día
- ✅ Búsqueda por nombre o cédula

### 3.6 Dashboard
- ✅ Total de personal registrado
- ✅ Total de estudiantes registrados
- ✅ Asistencias del día
- ✅ Tabla de asistencias recientes

---

## 4. Arquitectura

```
/app
├── backend/               # FastAPI + MongoDB
│   ├── server.py          # API principal
│   └── .env               # Configuración
├── frontend/              # React + Tailwind
│   ├── src/
│   │   ├── pages/         # Páginas (Scanner, Login, Register, Admin)
│   │   ├── layouts/       # AdminLayout
│   │   ├── context/       # AuthContext
│   │   └── components/ui/ # Shadcn components
│   └── .env               # REACT_APP_BACKEND_URL
└── memory/
    └── PRD.md             # Este documento
```

### Stack Tecnológico
- **Backend**: FastAPI, Python 3.11, MongoDB, PyJWT, bcrypt, qrcode
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, html5-qrcode
- **Database**: MongoDB

---

## 5. APIs Implementadas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/auth/register` | POST | Registrar admin |
| `/api/auth/login` | POST | Login |
| `/api/auth/me` | GET | Info del admin actual |
| `/api/personal` | GET/POST | Listar/Crear personal |
| `/api/personal/{id}` | GET/PUT/DELETE | CRUD personal |
| `/api/estudiantes` | GET/POST | Listar/Crear estudiantes |
| `/api/estudiantes/{id}` | GET/PUT/DELETE | CRUD estudiantes |
| `/api/asistencia` | POST | Registrar asistencia |
| `/api/asistencias` | GET | Listar asistencias |
| `/api/asistencias/hoy` | GET | Asistencias del día |
| `/api/stats` | GET | Estadísticas |

---

## 6. Backlog Priorizado

### P0 - Crítico (Implementado)
- [x] Escáner QR funcional
- [x] CRUD Personal y Estudiantes
- [x] Generación de QR
- [x] Registro de asistencias
- [x] Autenticación admin

### P1 - Alta Prioridad (Pendiente)
- [ ] Exportar asistencias a Excel/PDF
- [ ] Reportes estadísticos por período
- [ ] Impresión masiva de QR

### P2 - Media Prioridad
- [ ] Notificaciones de asistencia tardía
- [ ] Múltiples turnos (mañana/tarde)
- [ ] Historial de cambios (auditoría)

### P3 - Baja Prioridad
- [ ] App móvil nativa
- [ ] Integración con sistema de notas
- [ ] Dashboard con gráficos avanzados

---

## 7. Próximos Pasos

1. **Exportar datos**: Agregar función para exportar asistencias a Excel
2. **Reportes**: Crear vista de reportes con gráficos de asistencia
3. **Impresión QR**: Permitir impresión múltiple de códigos QR
4. **Respaldo**: Implementar backup automático de la base de datos

---

## 8. Credenciales de Prueba

- **Admin**: admin@test.com / password123

---

*Última actualización: 2025-12-28*
