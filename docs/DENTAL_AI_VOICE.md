# Odontograma, IA y asistente de voz (Dentifusion)

## Ideas para preparar el odontograma (`df_patient_odontogram`) hacia IA

1. **Contrato de datos estable**  
   - Documentar el esquema JSON de `chart_data` (versionado, p. ej. `schema_version`).  
   - Mantener `line_ids` como proyección indexable de ese JSON (ya existe `action_sync_lines_from_chart`).

2. **Campos de trazabilidad** (ampliados en `df_dental_voice_assistant` sobre `df.patient.odontogram.line`)  
   - `clinical_capture_source`: manual / voz / IA / importación.  
   - `last_voice_event_id`: enlace al último evento que modificó la pieza.

3. **Identificadores externos**  
   - `external_uuid` o `integration_ref` en línea de odontograma para correlacionar con motores externos (Alexa, FHIR, etc.) sin duplicar lógica clínica.

4. **Catálogo de hallazgos**  
   - Sustituir o complementar `status` Selection con un `Many2one` opcional a `df.dental.finding.type` (código, sinónimos multilenguaje) para que NLP mapee a IDs estables.

5. **Superficies normalizadas**  
   - Modelo o JSON con códigos FDI + superficies (O, M, D, V, L…) validados; hoy las superficies en procedimientos/plan son texto libre.

6. **API interna**  
   - Método único `apply_tooth_update(patient, tooth_code, vals, source='api')` que actualice chart + líneas + chatter; la voz/IA solo llaman a eso.

7. **No duplicar historia clínica**  
   - La “verdad” sigue en encuentro, procedimientos y plan; el odontograma es vista estructurada + estado por pieza.

---

## Addon `df_dental_voice_assistant`

Módulo MVP que implementa:

- `df.dental.voice.session` — contexto de captura (paciente, cita, encuentro, canal).  
- `df.dental.voice.event` — cada comando/transcripción, intención, payload JSON, estado de ejecución.  
- `df.dental.voice.command.rule` — reglas texto → intención sin desplegar código.  
- Políticas por compañía (`res.company`): auto-confirmación, exigir encuentro, permitir plan/procedimiento.  
- Despacho heurístico (español) hacia encuentro, `df.patient.odontogram.line`, `df.dental.procedure`, `df.dental.treatment.plan.line`.  
- Botón **Sesión voz** y contador en el formulario de encuentro.

**Instalación:** añadir `df_dental_voice_assistant` al `addons_path` y actualizar apps. Depende de `df_dental_procedure` y `df_dental_suite`.

**Próximos pasos sugeridos:** webhooks, integración Alexa/OpenClaw, transcripción vía servicio externo, y sustituir heurísticas por llamadas a un modelo de IA que devuelva JSON ya mapeado a los payloads.

---

## Convivencia con `df_dental_voice_temp`

`df_dental_voice_temp` fue un prototipo centrado en odontograma. Este módulo es la **capa clínica completa** descrita en tu documento; a medio plazo conviene migrar flujos del temp aquí y deprecar el temp.
