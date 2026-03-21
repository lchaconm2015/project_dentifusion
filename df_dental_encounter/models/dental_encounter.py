# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext


class DentalEncounter(models.Model):
    _name = "df.dental.encounter"
    _description = "Encuentro clínico dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )

    patient_id = fields.Many2one(
        "df.patient.registration",
        string="Paciente",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    appointment_id = fields.Many2one(
        "df.dental.appointment",
        string="Cita",
        ondelete="set null",
        tracking=True,
    )
    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo",
        required=True,
        tracking=True,
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
    )
    assistant_id = fields.Many2one(
        "res.users",
        string="Asistente",
        domain=[("share", "=", False)],
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    date_start = fields.Datetime(string="Inicio", required=True, default=fields.Datetime.now, tracking=True)
    date_end = fields.Datetime(string="Fin")
    encounter_date = fields.Date(
        string="Día (agenda)",
        compute="_compute_encounter_date",
        store=True,
        index=True,
    )
    duration_minutes = fields.Integer(
        string="Duración (min)",
        compute="_compute_duration_minutes",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_progress", "En curso"),
            ("done", "Cerrado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )

    consultation_type = fields.Selection(
        [
            ("first_time", "Primera vez"),
            ("follow_up", "Control / seguimiento"),
            ("emergency", "Urgencia"),
            ("evaluation", "Evaluación"),
            ("procedure", "Procedimiento"),
            ("control", "Control"),
        ],
        string="Tipo de consulta",
        default="follow_up",
        required=True,
    )
    specialty_id = fields.Many2one("df.dental.specialty", string="Especialidad")
    chief_complaint = fields.Text(string="Motivo de consulta")

    subjective_note = fields.Text(string="Subjetivo (S)")
    objective_note = fields.Text(string="Objetivo (O)")
    assessment_note = fields.Text(string="Análisis (A)")
    plan_note = fields.Text(string="Plan (P)")
    clinical_note = fields.Html(string="Nota clínica")

    prescription_note = fields.Text(string="Prescripción / medicación")
    recommendation_note = fields.Text(string="Recomendaciones")
    next_visit_note = fields.Text(string="Próxima visita")
    closure_summary = fields.Text(string="Resumen de cierre")

    data_source = fields.Selection(
        [
            ("manual", "Manual"),
            ("alexa", "Alexa / voz"),
            ("ai", "IA"),
            ("mixed", "Mixto"),
        ],
        string="Origen de datos",
        default="manual",
    )
    voice_transcript = fields.Text(string="Transcripción voz")
    ai_summary = fields.Text(string="Resumen IA")
    transcription_status = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("processed", "Procesado"),
            ("error", "Error"),
        ],
        string="Estado transcripción",
        default="pending",
    )

    is_signed = fields.Boolean(string="Firmado", tracking=True)
    signed_by = fields.Many2one("res.users", string="Firmado por", readonly=True)
    signed_datetime = fields.Datetime(string="Fecha firma", readonly=True)

    diagnosis_ids = fields.One2many(
        "df.dental.encounter.diagnosis",
        "encounter_id",
        string="Diagnósticos",
    )
    procedure_ids = fields.One2many(
        "df.dental.encounter.procedure",
        "encounter_id",
        string="Procedimientos",
    )

    active = fields.Boolean(default=True)

    @api.depends("date_start")
    def _compute_encounter_date(self):
        for rec in self:
            if rec.date_start:
                rec.encounter_date = fields.Datetime.context_timestamp(
                    rec, rec.date_start
                ).date()
            else:
                rec.encounter_date = False

    @api.depends("date_start", "date_end")
    def _compute_duration_minutes(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end > rec.date_start:
                delta = rec.date_end - rec.date_start
                rec.duration_minutes = int(delta.total_seconds() // 60)
            else:
                rec.duration_minutes = 0

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(_("La fecha de fin debe ser posterior al inicio."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nuevo")) in (False, _("Nuevo")):
                vals["name"] = self.env["ir.sequence"].next_by_code("df.dental.encounter") or _("Nuevo")
        return super().create(vals_list)

    def _is_clinical_manager(self):
        return self.env.user.has_group("df_dental_encounter.group_df_dental_clinical_manager")

    def _is_locked_done(self):
        self.ensure_one()
        return self.state == "done" and not self._is_clinical_manager()

    def write(self, vals):
        bypass = self.env.context.get("df_dental_encounter_unlock")
        for rec in self:
            if rec._is_locked_done() and not bypass:
                allowed = {"message_ids", "message_follower_ids", "activity_ids"}
                if set(vals) - allowed:
                    raise UserError(_("El encuentro cerrado solo puede modificarse por un gestor clínico."))
        return super().write(vals)

    def _validate_before_done(self):
        for rec in self:
            has_soap = any(
                [
                    (rec.subjective_note or "").strip(),
                    (rec.objective_note or "").strip(),
                    (rec.assessment_note or "").strip(),
                    (rec.plan_note or "").strip(),
                ]
            )
            plain_note = (html2plaintext(rec.clinical_note or "") or "").strip()
            has_html = bool(plain_note)
            has_rec = (rec.recommendation_note or "").strip()
            if not (
                has_soap
                or has_html
                or rec.diagnosis_ids
                or rec.procedure_ids
                or has_rec
            ):
                raise UserError(
                    _(
                        "Para cerrar el encuentro debe registrar al menos: nota clínica o SOAP, "
                        "un diagnóstico, un procedimiento o recomendaciones."
                    )
                )

    def action_start(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Solo borradores pueden iniciarse."))
            rec.state = "in_progress"

    def action_done(self):
        for rec in self:
            if rec.state not in ("draft", "in_progress"):
                raise UserError(_("El encuentro no puede cerrarse desde este estado."))
            rec._validate_before_done()
            rec.state = "done"
            if rec.date_end and rec.date_end < fields.Datetime.now():
                pass
            elif not rec.date_end:
                rec.date_end = fields.Datetime.now()
            if rec.appointment_id and rec.appointment_id.state not in ("done", "cancelled"):
                rec.appointment_id.action_mark_done()

    def action_cancel(self):
        for rec in self:
            if rec.state == "done":
                raise UserError(_("No puede cancelar un encuentro ya cerrado."))
            rec.state = "cancelled"

    def action_reset_draft(self):
        if not self._is_clinical_manager():
            raise UserError(_("Solo un gestor clínico puede reabrir el encuentro."))
        for rec in self:
            rec.write(
                {
                    "state": "draft",
                    "is_signed": False,
                    "signed_by": False,
                    "signed_datetime": False,
                }
            )

    def action_sign(self):
        for rec in self:
            if rec.state != "done":
                raise UserError(_("Solo puede firmar encuentros cerrados."))
            rec.write(
                {
                    "is_signed": True,
                    "signed_by": self.env.user.id,
                    "signed_datetime": fields.Datetime.now(),
                }
            )

    def action_open_patient(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Paciente"),
            "res_model": "df.patient.registration",
            "view_mode": "form",
            "res_id": self.patient_id.id,
        }

    def action_open_appointment(self):
        self.ensure_one()
        if not self.appointment_id:
            raise UserError(_("No hay cita vinculada."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Cita"),
            "res_model": "df.dental.appointment",
            "view_mode": "form",
            "res_id": self.appointment_id.id,
        }

    def action_open_odontogram(self):
        self.ensure_one()
        patient = self.patient_id
        if hasattr(patient, "action_open_odontogram"):
            return patient.action_open_odontogram()
        raise UserError(_("Instale el módulo de odontograma para abrir la ficha gráfica."))

    def action_create_treatment_plan(self):
        raise UserError(_("Plan de tratamiento: pendiente de módulo dedicado (fase 2)."))
