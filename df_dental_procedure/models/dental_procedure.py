# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DentalProcedure(models.Model):
    _name = "df.dental.procedure"
    _description = "Procedimiento clínico dental ejecutado"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "performed_date desc, planned_date desc, id desc"

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
    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    appointment_id = fields.Many2one(
        "df.dental.appointment",
        string="Cita",
        related="encounter_id.appointment_id",
        store=True,
        readonly=True,
    )
    treatment_plan_id = fields.Many2one(
        "df.dental.treatment.plan",
        string="Plan de tratamiento",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    treatment_plan_line_id = fields.Many2one(
        "df.dental.treatment.plan.line",
        string="Línea del plan",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    odontogram_line_id = fields.Many2one(
        "df.patient.odontogram.line",
        string="Pieza odontograma",
        ondelete="set null",
    )

    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo",
        required=True,
        domain=[("share", "=", False)],
        default=lambda self: self.env.user,
        tracking=True,
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

    planned_date = fields.Datetime(string="Fecha planificada")
    performed_date = fields.Datetime(string="Fecha realización")
    date_start = fields.Datetime(string="Inicio")
    date_end = fields.Datetime(string="Fin")
    duration_minutes = fields.Integer(
        string="Duración (min)",
        compute="_compute_duration_minutes",
        store=True,
    )

    procedure_code = fields.Char(string="Código")
    procedure_name = fields.Char(string="Procedimiento", required=True)
    description = fields.Text(string="Descripción")

    procedure_category = fields.Selection(
        [
            ("diagnostic", "Diagnóstico"),
            ("preventive", "Preventivo"),
            ("restorative", "Restaurador"),
            ("surgery", "Cirugía"),
            ("endodontics", "Endodoncia"),
            ("periodontics", "Periodoncia"),
            ("prosthodontics", "Prótesis"),
            ("orthodontics", "Ortodoncia"),
            ("control", "Control"),
            ("hygiene", "Higiene"),
        ],
        string="Categoría",
        default="restorative",
    )

    tooth_code = fields.Char(string="Pieza")
    surface_codes = fields.Char(string="Superficies")
    quadrant = fields.Selection(
        [
            ("ur", "C. sup. der."),
            ("ul", "C. sup. izq."),
            ("lr", "C. inf. der."),
            ("ll", "C. inf. izq."),
        ],
        string="Cuadrante",
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("planned", "Planificado"),
            ("ready", "Listo"),
            ("in_progress", "En curso"),
            ("performed", "Realizado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )

    clinical_result = fields.Text(string="Resultado clínico")
    complications = fields.Text(string="Complicaciones")
    post_op_instructions = fields.Text(string="Indicaciones postoperatorias")

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    estimated_fee = fields.Monetary(string="Honorario estimado", currency_field="currency_id")
    actual_fee = fields.Monetary(string="Honorario real", currency_field="currency_id")

    data_source = fields.Selection(
        [
            ("manual", "Manual"),
            ("alexa", "Voz"),
            ("ai", "IA"),
            ("mixed", "Mixto"),
        ],
        string="Origen datos",
        default="manual",
    )
    voice_transcript = fields.Text(string="Transcripción")
    ai_summary = fields.Text(string="Resumen IA")

    is_validated = fields.Boolean(string="Validado")
    validated_by = fields.Many2one("res.users", string="Validado por", readonly=True)
    validated_datetime = fields.Datetime(string="Fecha validación", readonly=True)

    active = fields.Boolean(default=True)

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
                vals["name"] = self.env["ir.sequence"].next_by_code("df.dental.procedure") or _("Nuevo")
            line_id = vals.get("treatment_plan_line_id")
            if line_id:
                line = self.env["df.dental.treatment.plan.line"].browse(line_id)
                vals.setdefault("treatment_plan_id", line.plan_id.id)
                vals.setdefault("patient_id", line.patient_id.id)
        records = super().create(vals_list)
        records._invalidate_plans()
        records._sync_plan_line_progress()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_plans()
        if "state" in vals or vals.get("performed_date") or vals.get("actual_fee"):
            self._sync_plan_line_progress()
        return res

    def unlink(self):
        lines = self.mapped("treatment_plan_line_id")
        plans = self.mapped("treatment_plan_id")
        self._invalidate_plans()
        res = super().unlink()
        lines._refresh_from_procedures()
        plans.invalidate_recordset(
            ["estimated_amount", "accepted_amount", "executed_amount", "progress_percent", "accepted_line_count", "completed_line_count"]
        )
        return res

    def _invalidate_plans(self):
        plans = self.mapped("treatment_plan_id")
        plans.invalidate_recordset(
            ["estimated_amount", "accepted_amount", "executed_amount", "progress_percent", "accepted_line_count", "completed_line_count"]
        )

    def _sync_plan_line_progress(self):
        for rec in self.filtered("treatment_plan_line_id"):
            rec.treatment_plan_line_id._refresh_from_procedures()

    @api.model
    def _prepare_from_plan_line_vals(self, line, encounter=None):
        return {
            "patient_id": line.patient_id.id,
            "treatment_plan_id": line.plan_id.id,
            "treatment_plan_line_id": line.id,
            "dentist_id": line.dentist_id.id if line.dentist_id else line.plan_id.dentist_id.id,
            "company_id": line.plan_id.company_id.id,
            "currency_id": line.plan_id.currency_id.id,
            "procedure_code": line.treatment_code,
            "procedure_name": line.treatment_name,
            "description": line.description,
            "tooth_code": line.tooth_code,
            "surface_codes": line.surface_codes,
            "quadrant": line.quadrant,
            "odontogram_line_id": line.odontogram_line_id.id,
            "estimated_fee": line.estimated_subtotal,
            "planned_date": fields.Datetime.now(),
            "state": "planned",
            "encounter_id": encounter.id if encounter else line.encounter_id.id,
        }

    def _check_required_for_performed(self):
        for rec in self:
            if not rec.encounter_id:
                raise UserError(_("Debe indicar el encuentro antes de marcar como realizado."))
            if not rec.performed_date:
                raise UserError(_("Indique la fecha de realización."))
            if not (rec.clinical_result or "").strip() and not (rec.description or "").strip():
                raise UserError(_("Registre un resultado clínico o una descripción del procedimiento."))

    def action_plan(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Solo borradores pueden planificarse."))
            rec.state = "planned"
            if not rec.planned_date:
                rec.planned_date = fields.Datetime.now()

    def action_ready(self):
        for rec in self:
            if rec.state != "planned":
                raise UserError(_("Solo procedimientos planificados pueden marcarse listos."))
            rec.state = "ready"

    def action_start(self):
        for rec in self:
            if rec.state not in ("planned", "ready"):
                raise UserError(_("Estado no válido para iniciar."))
            rec.write(
                {
                    "state": "in_progress",
                    "date_start": fields.Datetime.now(),
                }
            )

    def action_performed(self):
        for rec in self:
            if rec.state not in ("planned", "ready", "in_progress", "draft"):
                raise UserError(_("Estado no válido para cierre."))
            rec._check_required_for_performed()
            vals = {
                "state": "performed",
                "performed_date": rec.performed_date or fields.Datetime.now(),
            }
            if not rec.date_end:
                vals["date_end"] = fields.Datetime.now()
            rec.write(vals)

    def action_cancel(self):
        for rec in self:
            if rec.state == "performed":
                raise UserError(_("No puede cancelar un procedimiento ya realizado."))
            rec.state = "cancelled"

    def action_validate(self):
        for rec in self:
            if rec.state != "performed":
                raise UserError(_("Solo procedimientos realizados pueden validarse."))
            rec.write(
                {
                    "is_validated": True,
                    "validated_by": self.env.user.id,
                    "validated_datetime": fields.Datetime.now(),
                }
            )

    def action_open_encounter(self):
        self.ensure_one()
        if not self.encounter_id:
            raise UserError(_("No hay encuentro vinculado."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Encuentro"),
            "res_model": "df.dental.encounter",
            "view_mode": "form",
            "res_id": self.encounter_id.id,
        }

    def action_open_treatment_plan(self):
        self.ensure_one()
        if not self.treatment_plan_id:
            raise UserError(_("No hay plan vinculado."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Plan"),
            "res_model": "df.dental.treatment.plan",
            "view_mode": "form",
            "res_id": self.treatment_plan_id.id,
        }

    def action_open_patient(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Paciente"),
            "res_model": "df.patient.registration",
            "view_mode": "form",
            "res_id": self.patient_id.id,
        }

    def action_open_odontogram(self):
        self.ensure_one()
        if hasattr(self.patient_id, "action_open_odontogram"):
            return self.patient_id.action_open_odontogram()
        raise UserError(_("Odontograma no disponible."))
