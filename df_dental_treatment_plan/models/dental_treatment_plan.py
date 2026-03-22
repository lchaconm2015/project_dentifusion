# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalTreatmentPlan(models.Model):
    _name = "df.dental.treatment.plan"
    _description = "Plan de tratamiento dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "plan_date desc, id desc"

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
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        related="patient_id.partner_id",
        store=True,
        readonly=True,
    )
    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro origen",
        ondelete="set null",
        tracking=True,
    )
    appointment_id = fields.Many2one(
        "df.dental.appointment",
        string="Cita",
        related="encounter_id.appointment_id",
        store=True,
        readonly=True,
    )
    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo responsable",
        required=True,
        tracking=True,
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    plan_date = fields.Date(string="Fecha del plan", default=fields.Date.context_today, required=True)
    valid_until = fields.Date(string="Vigente hasta")

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("proposed", "Propuesto"),
            ("partially_accepted", "Parcialmente aceptado"),
            ("accepted", "Aceptado"),
            ("in_progress", "En ejecución"),
            ("completed", "Completado"),
            ("cancelled", "Cancelado"),
            ("rejected", "Rechazado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )

    chief_complaint = fields.Text(string="Motivo de consulta")
    clinical_summary = fields.Text(string="Resumen clínico")
    observations = fields.Text(string="Observaciones")

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    estimated_amount = fields.Monetary(
        string="Total estimado",
        compute="_compute_amounts_and_progress",
        store=True,
        currency_field="currency_id",
    )
    accepted_amount = fields.Monetary(
        string="Total aceptado",
        compute="_compute_amounts_and_progress",
        store=True,
        currency_field="currency_id",
    )
    executed_amount = fields.Monetary(
        string="Total ejecutado",
        compute="_compute_amounts_and_progress",
        store=True,
        currency_field="currency_id",
        help="Suma de honorarios reales en procedimientos vinculados (módulo df_dental_procedure).",
    )

    line_ids = fields.One2many(
        "df.dental.treatment.plan.line",
        "plan_id",
        string="Líneas",
    )
    progress_percent = fields.Float(
        string="Progreso (%)",
        compute="_compute_amounts_and_progress",
        store=True,
        digits=(16, 2),
    )
    accepted_line_count = fields.Integer(
        string="Líneas aceptadas",
        compute="_compute_amounts_and_progress",
        store=True,
    )
    completed_line_count = fields.Integer(
        string="Líneas completadas",
        compute="_compute_amounts_and_progress",
        store=True,
    )

    patient_approved = fields.Boolean(string="Aprobación paciente registrada")
    patient_approval_date = fields.Datetime(string="Fecha aprobación paciente")
    approved_by_user_id = fields.Many2one(
        "res.users",
        string="Registrado por",
        readonly=True,
    )

    notes = fields.Html(string="Notas")
    active = fields.Boolean(default=True)

    @api.depends(
        "line_ids",
        "line_ids.estimated_subtotal",
        "line_ids.is_accepted",
        "line_ids.state",
        "line_ids.estimated_unit_price",
        "line_ids.qty",
    )
    def _compute_amounts_and_progress(self):
        try:
            Procedure = self.env["df.dental.procedure"]
        except KeyError:
            Procedure = None
        for rec in self:
            lines = rec.line_ids
            rec.estimated_amount = sum(lines.mapped("estimated_subtotal"))
            accepted_lines = lines.filtered(lambda l: l.is_accepted and l.state != "rejected")
            rec.accepted_amount = sum(accepted_lines.mapped("estimated_subtotal"))
            rec.accepted_line_count = len(accepted_lines)
            rec.completed_line_count = len(lines.filtered(lambda l: l.state == "completed"))
            if accepted_lines:
                rec.progress_percent = (rec.completed_line_count / len(accepted_lines)) * 100.0
            elif lines:
                rec.progress_percent = (rec.completed_line_count / len(lines)) * 100.0
            else:
                rec.progress_percent = 0.0
            if Procedure:
                procs = Procedure.search(
                    [("treatment_plan_id", "=", rec.id), ("state", "=", "performed")]
                )
                rec.executed_amount = sum(procs.mapped("actual_fee"))
            else:
                rec.executed_amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nuevo")) in (False, _("Nuevo")):
                vals["name"] = self.env["ir.sequence"].next_by_code("df.dental.treatment.plan") or _("Nuevo")
        return super().create(vals_list)

    def _require_manager(self):
        if not self.env.user.has_group("df_dental_treatment_plan.group_df_dental_treatment_manager"):
            raise UserError(_("Solo un gestor clínico puede realizar esta acción."))

    def action_propose(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Solo borradores pueden proponerse."))
            if not rec.line_ids:
                raise UserError(_("Agregue al menos una línea al plan."))
            rec.line_ids.filtered(lambda l: l.state == "draft").write({"state": "proposed"})
            rec.state = "proposed"

    def action_accept(self):
        for rec in self:
            if rec.state not in ("proposed", "partially_accepted", "draft"):
                raise UserError(_("Estado no válido para aceptación total."))
            rec.write(
                {
                    "state": "accepted",
                    "patient_approved": True,
                    "patient_approval_date": fields.Datetime.now(),
                    "approved_by_user_id": self.env.user.id,
                }
            )
            rec.line_ids.filtered(lambda l: l.state in ("draft", "proposed")).write(
                {"is_accepted": True, "accepted_date": fields.Datetime.now(), "state": "accepted"}
            )

    def action_partial_accept(self):
        for rec in self:
            if rec.state not in ("proposed", "draft"):
                raise UserError(_("Proponga el plan antes de marcar aceptación parcial."))
            if not rec.line_ids.filtered("is_accepted"):
                raise UserError(_("Marque como aceptadas las líneas correspondientes."))
            rec.state = "partially_accepted"
            rec.patient_approved = True
            rec.patient_approval_date = fields.Datetime.now()
            rec.approved_by_user_id = self.env.user.id

    def action_reject(self):
        for rec in self:
            if rec.state in ("completed", "cancelled"):
                raise UserError(_("No puede rechazar este plan."))
            rec.state = "rejected"
            rec.line_ids.write({"state": "rejected", "is_accepted": False})

    def action_start_execution(self):
        for rec in self:
            if rec.state not in ("accepted", "partially_accepted"):
                raise UserError(_("El plan debe estar aceptado o parcialmente aceptado."))
            rec.state = "in_progress"

    def action_complete(self):
        for rec in self:
            if rec.state != "in_progress":
                raise UserError(_("Solo planes en ejecución pueden completarse."))
            pending = rec.line_ids.filtered(
                lambda l: l.is_accepted and l.state not in ("completed", "cancelled", "rejected")
            )
            if pending:
                raise UserError(_("Aún hay líneas aceptadas sin completar."))
            rec.state = "completed"

    def action_cancel(self):
        self._require_manager()
        for rec in self:
            if rec.state in ("completed",):
                raise UserError(_("No puede cancelar un plan completado."))
            rec.state = "cancelled"
            rec.line_ids.filtered(lambda l: l.state not in ("completed",)).write({"state": "cancelled"})

    def action_open_patient(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Paciente"),
            "res_model": "df.patient.registration",
            "view_mode": "form",
            "res_id": self.patient_id.id,
        }

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

    def action_reset_draft(self):
        self._require_manager()
        for rec in self:
            if rec.state not in ("cancelled", "rejected", "proposed"):
                raise UserError(_("Solo ciertos estados pueden volver a borrador."))
            rec.state = "draft"
