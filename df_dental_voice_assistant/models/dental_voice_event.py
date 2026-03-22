# -*- coding: utf-8 -*-
import json
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalVoiceEvent(models.Model):
    _name = "df.dental.voice.event"
    _description = "Evento de voz o comando clínico"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Referencia", required=True, default=lambda self: _("Nuevo"))
    session_id = fields.Many2one(
        "df.dental.voice.session",
        string="Sesión",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="session_id.company_id",
        store=True,
        readonly=True,
    )
    patient_id = fields.Many2one(
        related="session_id.patient_id",
        store=True,
        readonly=True,
    )
    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro",
        ondelete="set null",
        index=True,
    )
    channel = fields.Selection(
        related="session_id.channel",
        store=True,
        readonly=True,
    )
    source_type = fields.Selection(
        [
            ("text_command", "Comando texto"),
            ("transcript", "Transcripción"),
            ("audio_note", "Nota de audio"),
            ("structured_payload", "Payload estructurado"),
            ("ai_result", "Resultado IA"),
        ],
        string="Tipo de origen",
        default="text_command",
        required=True,
    )
    raw_text = fields.Text(string="Texto original", required=True)
    normalized_text = fields.Text(string="Texto normalizado", readonly=True)
    audio_url = fields.Char(string="URL audio externo")
    audio_attachment_id = fields.Many2one("ir.attachment", string="Adjunto audio")

    intent = fields.Selection(
        [
            ("open_session", "Abrir sesión"),
            ("close_session", "Cerrar sesión"),
            ("add_clinical_note", "Nota clínica"),
            ("add_odontogram_finding", "Hallazgo odontograma"),
            ("add_procedure", "Procedimiento"),
            ("add_treatment_plan_line", "Línea plan tratamiento"),
            ("update_encounter", "Actualizar encuentro"),
            ("unknown", "Desconocido"),
        ],
        string="Intención",
        default="unknown",
    )
    confidence_score = fields.Float(string="Confianza", digits=(3, 2))
    parsed_payload = fields.Text(string="Payload (JSON)")

    execution_status = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("processed", "Procesado"),
            ("confirmed", "Confirmado"),
            ("corrected", "Corregido"),
            ("rejected", "Rechazado"),
            ("error", "Error"),
        ],
        string="Estado ejecución",
        default="pending",
        required=True,
        tracking=True,
    )
    execution_message = fields.Text(string="Mensaje ejecución")
    target_model = fields.Char(string="Modelo destino")
    target_res_id = fields.Integer(string="ID registro destino")

    ai_summary = fields.Text(string="Resumen IA")
    ai_model_name = fields.Char(string="Modelo IA")

    processed_by_user_id = fields.Many2one("res.users", string="Procesado por", readonly=True)
    processed_datetime = fields.Datetime(string="Fecha procesamiento", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            session = None
            if vals.get("session_id"):
                session = self.env["df.dental.voice.session"].browse(vals["session_id"])
            if session and not vals.get("encounter_id") and session.encounter_id:
                vals.setdefault("encounter_id", session.encounter_id.id)
            raw = vals.get("raw_text") or ""
            vals["normalized_text"] = self._normalize_text_static(raw)
        records = super().create(vals_list)
        for rec in records:
            if rec.name in (False, _("Nuevo")):
                rec.name = "%s #%s" % (rec.session_id.name or _("Voz"), rec.id)
        return records

    @staticmethod
    def _normalize_text_static(text):
        if not text:
            return ""
        return " ".join(text.lower().strip().split())

    def _normalize_text(self, text):
        return self._normalize_text_static(text)

    def _match_command_rules(self, norm):
        Rule = self.env["df.dental.voice.command.rule"]
        rules = Rule.search([("active", "=", True)], order="priority desc, sequence, id")
        for rule in rules:
            trig = (rule.trigger_text or "").lower().strip()
            if trig and trig in norm:
                return rule.intent, 0.92
        return None, 0.0

    def _detect_intent_heuristic(self, norm):
        if any(k in norm for k in ("cerrar sesión", "cerrar sesion", "finalizar consulta", "terminar sesión", "terminar sesion")):
            return "close_session", 0.85
        if any(
            k in norm
            for k in (
                "abrir sesión",
                "abrir sesion",
                "iniciar sesión",
                "iniciar sesion",
            )
        ):
            return "open_session", 0.8
        if any(
            k in norm
            for k in (
                "nota clínica",
                "nota clinica",
                "dictado",
                "paciente refiere",
                "agregar nota",
            )
        ):
            return "add_clinical_note", 0.75
        if any(
            k in norm
            for k in (
                "caries",
                "odontograma",
                "pieza",
                "hallazgo",
                "oclusal",
                "mesial",
                "distal",
            )
        ):
            return "add_odontogram_finding", 0.65
        if "procedimiento" in norm or "profilaxis" in norm or "restauración" in norm or "restauracion" in norm:
            return "add_procedure", 0.65
        if any(k in norm for k in ("plan de tratamiento", "línea del plan", "linea del plan", "plan tratamiento")):
            return "add_treatment_plan_line", 0.6
        if "encuentro" in norm or "soap" in norm or "motivo de consulta" in norm:
            return "update_encounter", 0.55
        return "unknown", 0.2

    def _extract_tooth_code(self, norm):
        patterns = [
            r"\b(?:pieza|diente|número|numero)\s*(\d{2})\b",
            r"\b(?:la|el)\s*(\d{2})\b",
            r"\b(\d{2})\b",
        ]
        for pat in patterns:
            m = re.search(pat, norm)
            if m:
                return m.group(1)
        return None

    def _extract_surfaces(self, norm):
        surf = []
        mapping = {
            "oclusal": "O",
            "incisal": "I",
            "mesial": "M",
            "distal": "D",
            "vestibular": "V",
            "lingual": "L",
            "palatina": "P",
        }
        for word, code in mapping.items():
            if word in norm:
                surf.append(code)
        return ",".join(surf)

    def _parse_payload(self, intent, norm):
        payload = {
            "tooth_code": self._extract_tooth_code(norm),
            "surface_codes": self._extract_surfaces(norm),
            "finding_keywords": norm[:500],
        }
        if intent == "add_procedure":
            payload["procedure_name"] = norm[:200]
        if intent == "add_treatment_plan_line":
            payload["treatment_name"] = norm[:200]
        if intent == "add_clinical_note":
            payload["note_text"] = self.raw_text or ""
        return payload

    def _company_voice_policy(self):
        return self.session_id.company_id

    def _validate_minimum_context(self):
        self.ensure_one()
        comp = self._company_voice_policy()
        if not comp.voice_assistant_enabled:
            raise UserError(_("El asistente de voz está deshabilitado para esta compañía."))
        if comp.voice_require_encounter and self.intent not in (
            "open_session",
            "close_session",
            "unknown",
        ):
            if not self.encounter_id:
                raise UserError(
                    _(
                        "Se requiere un encuentro clínico activo para ejecutar esta intención. "
                        "Vincule la sesión de voz a un encuentro."
                    )
                )

    def _append_clinical_note_to_encounter(self, note_text):
        enc = self.encounter_id
        stamp = fields.Datetime.now()
        block = _("\n[%s · Voz] %s") % (fields.Datetime.to_string(stamp), note_text)
        enc.subjective_note = (enc.subjective_note or "") + block
        if enc.data_source == "manual":
            enc.data_source = "mixed"
        elif enc.data_source not in ("alexa", "ai", "mixed"):
            enc.data_source = "alexa"
        if enc.voice_transcript:
            enc.voice_transcript += "\n" + (self.raw_text or "")
        else:
            enc.voice_transcript = self.raw_text or ""

    def _get_or_create_odontogram(self, patient):
        Odontogram = self.env["df.patient.odontogram"]
        odo = Odontogram.search([("patient_id", "=", patient.id)], limit=1)
        if not odo:
            odo = Odontogram.create({"patient_id": patient.id})
            odo.action_sync_lines_from_chart()
        return odo

    def _create_odontogram_line_from_payload(self, payload):
        patient = self.patient_id
        tooth = payload.get("tooth_code")
        if not tooth:
            raise UserError(_("No se identificó número de pieza en el comando."))
        odo = self._get_or_create_odontogram(patient)
        Line = self.env["df.patient.odontogram.line"]
        line = Line.search(
            [("odontogram_id", "=", odo.id), ("tooth_code", "=", tooth)],
            limit=1,
        )
        note_extra = ""
        if payload.get("surface_codes"):
            note_extra += _(" Superficies: %s.") % payload["surface_codes"]
        notes = ((line.notes if line else "") or "") + note_extra
        if self.raw_text:
            notes += "\n" + (self.raw_text[:500])
        vals = {
            "status": "pathology",
            "notes": notes.strip(),
            "clinical_capture_source": "voice",
            "last_voice_event_id": self.id,
        }
        if line:
            line.write(vals)
            return line
        vals.update(
            {
                "odontogram_id": odo.id,
                "tooth_code": tooth,
            }
        )
        return Line.create(vals)

    def _create_procedure_from_payload(self, payload):
        comp = self._company_voice_policy()
        if not comp.voice_allow_procedure_creation:
            raise UserError(_("La compañía no permite crear procedimientos por voz."))
        name = (payload.get("procedure_name") or self.raw_text or _("Procedimiento (voz)"))[:200]
        proc = self.env["df.dental.procedure"].create(
            {
                "patient_id": self.patient_id.id,
                "encounter_id": self.encounter_id.id,
                "dentist_id": self.session_id.dentist_id.id,
                "company_id": self.session_id.company_id.id,
                "procedure_name": name,
                "description": self.raw_text,
                "state": "draft",
                "data_source": "alexa",
                "voice_transcript": self.raw_text,
                "tooth_code": payload.get("tooth_code") or False,
                "surface_codes": payload.get("surface_codes") or False,
            }
        )
        return proc

    def _get_or_create_draft_plan(self):
        Plan = self.env["df.dental.treatment.plan"]
        comp = self._company_voice_policy()
        if not comp.voice_allow_plan_creation:
            raise UserError(_("La compañía no permite crear líneas de plan por voz."))
        enc = self.encounter_id
        plan = Plan.search(
            [
                ("encounter_id", "=", enc.id),
                ("state", "in", ("draft", "proposed", "partially_accepted")),
            ],
            limit=1,
            order="id desc",
        )
        if plan:
            return plan
        return Plan.create(
            {
                "patient_id": enc.patient_id.id,
                "encounter_id": enc.id,
                "dentist_id": enc.dentist_id.id,
                "company_id": enc.company_id.id,
                "state": "draft",
            }
        )

    def _create_treatment_plan_line_from_payload(self, payload):
        plan = self._get_or_create_draft_plan()
        name = (payload.get("treatment_name") or self.raw_text or _("Tratamiento (voz)"))[:200]
        line = self.env["df.dental.treatment.plan.line"].create(
            {
                "plan_id": plan.id,
                "treatment_name": name,
                "description": self.raw_text,
                "tooth_code": payload.get("tooth_code") or False,
                "surface_codes": payload.get("surface_codes") or False,
                "state": "draft",
                "dentist_id": self.session_id.dentist_id.id,
            }
        )
        return line

    def _execute_clinical_intent(self):
        """Ejecuta la acción clínica según intención y payload (sin comprobar auto_confirm)."""
        self.ensure_one()
        intent = self.intent
        payload = {}
        if self.parsed_payload:
            try:
                payload = json.loads(self.parsed_payload)
            except Exception:
                payload = {}

        self.target_model = ""
        self.target_res_id = 0
        self.execution_message = False

        if intent == "unknown":
            self.execution_message = _("Intención no reconocida; no se ejecutó ninguna acción clínica.")
            return

        self._validate_minimum_context()

        if intent == "open_session":
            self.execution_message = _("La sesión de voz ya está registrada en Odoo.")
            self.target_model = "df.dental.voice.session"
            self.target_res_id = self.session_id.id
            return

        if intent == "close_session":
            self.session_id.action_complete()
            self.execution_message = _("Sesión de voz completada.")
            self.target_model = "df.dental.voice.session"
            self.target_res_id = self.session_id.id
            return

        if intent == "add_clinical_note":
            note = payload.get("note_text") or self.raw_text
            self._append_clinical_note_to_encounter(note)
            self.execution_message = _("Nota añadida al encuentro (subjetivo / transcripción).")
            self.target_model = "df.dental.encounter"
            self.target_res_id = self.encounter_id.id
            return

        if intent == "add_odontogram_finding":
            line = self._create_odontogram_line_from_payload(payload)
            self.execution_message = _("Actualizada pieza en odontograma.")
            self.target_model = "df.patient.odontogram.line"
            self.target_res_id = line.id
            return

        if intent == "add_procedure":
            proc = self._create_procedure_from_payload(payload)
            self.execution_message = _("Procedimiento borrador creado.")
            self.target_model = "df.dental.procedure"
            self.target_res_id = proc.id
            return

        if intent == "add_treatment_plan_line":
            line = self._create_treatment_plan_line_from_payload(payload)
            self.execution_message = _("Línea de plan en borrador creada.")
            self.target_model = "df.dental.treatment.plan.line"
            self.target_res_id = line.id
            return

        if intent == "update_encounter":
            enc = self.encounter_id
            enc.chief_complaint = (enc.chief_complaint or "") + "\n" + (self.raw_text or "")
            if enc.data_source == "manual":
                enc.data_source = "mixed"
            self.execution_message = _("Encuentro actualizado (motivo / texto libre).")
            self.target_model = "df.dental.encounter"
            self.target_res_id = enc.id
            return

        self.execution_message = _("Sin manejador para esta intención.")

    def _dispatch_after_interpretation(self):
        """Aplica política auto_confirm: ejecuta o deja pendiente."""
        self.ensure_one()
        comp = self._company_voice_policy()
        auto = comp.voice_auto_confirm

        if self.intent == "unknown":
            self.execution_message = _(
                "Intención no reconocida; revise el texto o defina una regla de comando."
            )
            self.execution_status = "processed" if auto else "pending"
            return

        if not auto:
            self.execution_status = "pending"
            self.execution_message = _(
                "Interpretado. Pendiente de confirmación para ejecutar en el expediente."
            )
            return

        try:
            self._execute_clinical_intent()
            self.execution_status = "processed"
        except UserError as e:
            self.execution_status = "error"
            self.execution_message = e.args[0] if e.args else _("Error")
        except Exception as e:
            self.execution_status = "error"
            self.execution_message = str(e)

    def action_process(self):
        for rec in self:
            norm = rec.normalized_text or rec._normalize_text(rec.raw_text or "")
            intent, conf_rule = rec._match_command_rules(norm)
            if not intent:
                intent, conf_heur = rec._detect_intent_heuristic(norm)
                rec.confidence_score = conf_heur
            else:
                rec.confidence_score = conf_rule
            rec.intent = intent
            payload = rec._parse_payload(intent, norm)
            rec.parsed_payload = json.dumps(payload, ensure_ascii=False)
            rec._dispatch_after_interpretation()
            rec.processed_by_user_id = rec.env.user
            rec.processed_datetime = fields.Datetime.now()
        return True

    def action_confirm(self):
        for rec in self:
            if rec.execution_status != "pending":
                raise UserError(_("Solo puede confirmar eventos pendientes."))
            if rec.intent == "unknown":
                raise UserError(_("No puede confirmar un evento sin intención reconocida."))
            try:
                rec._execute_clinical_intent()
                rec.write(
                    {
                        "execution_status": "confirmed",
                        "processed_by_user_id": rec.env.user.id,
                        "processed_datetime": fields.Datetime.now(),
                    }
                )
            except UserError as e:
                rec.execution_status = "error"
                rec.execution_message = e.args[0] if e.args else _("Error")
            except Exception as e:
                rec.execution_status = "error"
                rec.execution_message = str(e)
        return True

    def action_reject(self):
        for rec in self:
            rec.write(
                {
                    "execution_status": "rejected",
                    "execution_message": (rec.execution_message or "")
                    + "\n"
                    + _("Rechazado por el usuario."),
                }
            )
        return True

    def action_correct(self):
        for rec in self:
            rec.execution_status = "corrected"
        return True

    def action_open_target_record(self):
        self.ensure_one()
        if not self.target_model or not self.target_res_id:
            raise UserError(_("No hay registro destino."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Registro vinculado"),
            "res_model": self.target_model,
            "view_mode": "form",
            "res_id": self.target_res_id,
        }
