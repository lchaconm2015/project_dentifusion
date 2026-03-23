# Configuración inicial del sistema (Suite dental Dentifusion)

Guía ordenada para dejar Odoo listo para usar la suite **df_*** en un entorno nuevo (Odoo 16).

---

## 1. Servidor y código

1. **Añadir el addon path** de este repositorio a la configuración de Odoo (`addons_path`), junto con los addons estándar de Odoo.
2. **Crear la base de datos** (si aún no existe) con idioma y zona horaria adecuados (recomendado: misma zona que la clínica).
3. Iniciar Odoo y entrar como **administrador**.

---

## 2. Activar aplicaciones base de Odoo

Instala al menos:

| Aplicación | Motivo |
|------------|--------|
| **Contactos** | Pacientes enlazan con `res.partner`. |
| **Calendario** | Citas dentales (`df_dental_appointment` depende de `calendar`). |
| **Correo electrónico / Conversaciones** (recomendado) | Chatter en citas, encuentros, procedimientos y notificaciones. |

*(Opcional según tu proyecto: Contabilidad, Ventas, Sitio web, etc.)*

---

## 3. Instalar módulos de la suite (orden recomendado)

Desde **Aplicaciones**, quitar el filtro “Aplicaciones” y buscar por nombre técnico o por “DF”.

**Orden lógico** (respeta dependencias; Odoo suele resolverlas solo):

1. `df_patient_registration` — Fichas de pacientes.  
2. `df_patient_odontogram` — Odontograma por paciente.  
3. `df_dental_appointment` — Agenda y citas.  
4. `df_dental_encounter` — Encuentros / consultas.  
5. `df_dental_treatment_plan` — Planes de tratamiento.  
6. `df_dental_procedure` — Procedimientos ejecutados.  
7. **`df_dental_suite`** — Menú unificado **“Suite dental”**.  
8. *(Opcional)* `df_dental_voice_assistant` — Asistente de voz / captura clínica.  

> **No instales** `df_dental_voice_temp` salvo que necesites ese prototipo concreto; la línea nueva es `df_dental_voice_assistant`.

Tras instalar, **actualiza la lista de aplicaciones** si añades módulos nuevos al servidor.

---

## 4. Compañía

1. **Ajustes → Usuarios y compañías → Compañías** (o edición desde la barra multi-compañía).  
2. Completar: nombre, dirección, NIF/CIF, moneda, zona horaria.  
3. Si instalaste **asistente de voz**: en la ficha de la compañía, pestaña **“Asistente voz dental”** (visible con perfil de gestor clínico):
   - Activar o desactivar el asistente.  
   - **Confirmar automáticamente eventos de voz**: en producción clínica suele ir en **desactivado** hasta validar el flujo; en pruebas puede ir en **activado**.  
   - **Exigir encuentro**: recomendado **activado** para no crear hallazgos sin contexto de consulta.  
   - Permitir creación de plan / procedimiento por voz según política de la clínica.

---

## 5. Usuarios y derechos (grupos)

En **Ajustes → Usuarios y compañías → Usuarios**, asigna perfiles según el rol real.

### Agenda y administración dental (`df_dental_appointment`)

| Grupo en Odoo | Uso típico |
|----------------|------------|
| **Recepción dental** | Agenda, citas (lectura amplia según reglas), sin rol clínico completo. |
| **Odontólogo** | Sus citas, Kanban, calendario, encuentros asignados a él. |
| **Gestor clínica dental** | Todas las citas, reset a borrador, visión global. |

### Clínica (`df_dental_encounter`)

| Grupo | Uso típico |
|--------|------------|
| **Asistente clínico dental** | Encuentros, SOAP, diagnósticos de encuentro, menú clínico amplio. |
| **Gestor clínico dental** | Todo lo anterior + reabrir encuentros cerrados, reglas amplias. |

### Plan y procedimientos

- **Usuario / gestor de plan de tratamiento** y **Usuario / gestor de procedimientos** según necesites separar quien propone planes vs. quien cierra u audita.

### Buenas prácticas

- Al menos **un usuario administrador** o **gestor** con **Gestor clínica dental** + **Gestor clínico dental** (y gestor de plan/procedimiento si aplica) para soporte y cierre de casos excepcionales.  
- Cada odontólogo: **Usuario interno** + **Odontólogo** + los grupos clínicos que deban usar (asistente clínico, usuario de plan/procedimiento, etc.).  
- Recepción: **Recepción dental** (y sin grupos clínicos si no deben ver notas clínicas).

---

## 6. Catálogos: Configuración clínica

En menú **Suite dental → Configuración clínica** (tras instalar `df_dental_suite`):

1. **Especialidades** — al menos las que uses en citas y encuentros.  
2. **Consultorios** y **Sillones / unidades** — opcionales pero útiles para agenda.  
3. **Tipos de cita / plantillas** — duraciones y especialidad sugerida si las usas.

No es obligatorio tenerlo todo el primer día, pero **especialidades** y **datos coherentes en citas** mejoran filtros e informes.

---

## 7. Secuencias y numeraciones

Los módulos crean secuencias al instalarse (citas, encuentros, planes, procedimientos, sesiones VOICE, etc.).  

Si necesitas otro prefijo o año:

**Ajustes → Técnico → Secuencias** (modo desarrollador) y buscar códigos como `df.dental.appointment`, `df.dental.encounter`, etc.

---

## 8. Calendario y recordatorios

- Las citas pueden generar eventos de **Calendario** según la lógica del módulo de citas.  
- Revisa que los **usuarios** tengan **correo** correcto si usarás notificaciones por email.

---

## 9. Comprobación rápida (flujo mínimo)

1. **Paciente**: Suite dental → Pacientes → Ficha de paciente (crear uno de prueba).  
2. **Cita**: Agenda → nueva cita, paciente, odontólogo, fechas, estado hasta **confirmada** si aplica.  
3. **Encuentro**: desde la cita o menú de encuentros → crear/iniciar consulta, completar nota o SOAP mínimo y **finalizar** según las reglas del módulo.  
4. **Odontograma**: desde paciente o encuentro → abrir odontograma y comprobar que carga.  
5. *(Si tienes voz)* Encuentro → **Sesión voz** → evento de prueba con texto claro (p. ej. nota clínica) → **Interpretar / procesar**.

Si algún paso falla, anota el mensaje de error y el módulo implicado.

---

## 10. Entornos múltiples (opcional)

- **Producción**: copia de seguridad de BD antes de `-u` masivos.  
- **Desarrollo**: misma versión de Odoo (16.x) y mismos módulos para evitar diferencias de vistas.

---

## Referencias en este repo

- Visión IA / voz y odontograma: `docs/DENTAL_AI_VOICE.md`  
- Módulo voz: `df_dental_voice_assistant/README.md`  

---

*Documento orientativo a la suite `project_dentifusion`. Ajusta nombres de menús si tu traducción de Odoo difiere.*
