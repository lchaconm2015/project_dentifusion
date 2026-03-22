# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DentalTreatmentPlanLine(models.Model):
    _name = "df.dental.treatment.plan.line"
    _description = "Línea de plan de tratamiento dental"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one(
        "df.dental.treatment.plan",
        string="Plan",
        required=True,
        ondelete="cascade",
        index=True,
    )
    patient_id = fields.Many2one(
        related="plan_id.patient_id",
        store=True,
        readonly=True,
    )
    encounter_id = fields.Many2one(
        related="plan_id.encounter_id",
        store=True,
        readonly=True,
    )

    sequence = fields.Integer(default=10)
    phase = fields.Selection(
        [
            ("phase_1", "Fase 1"),
            ("phase_2", "Fase 2"),
            ("phase_3", "Fase 3"),
            ("other", "Otra"),
        ],
        string="Fase",
        default="phase_1",
    )
    priority = fields.Selection(
        [
            ("low", "Baja"),
            ("medium", "Media"),
            ("high", "Alta"),
            ("urgent", "Urgente"),
        ],
        string="Prioridad",
        default="medium",
        required=True,
    )

    treatment_code = fields.Char(string="Código tratamiento")
    treatment_name = fields.Char(string="Tratamiento", required=True)
    description = fields.Text(string="Descripción")

    tooth_code = fields.Char(string="Pieza")
    surface_codes = fields.Char(string="Superficies", help="Ej. O,M,D")
    quadrant = fields.Selection(
        [
            ("ur", "Cuadrante superior derecho"),
            ("ul", "Cuadrante superior izquierdo"),
            ("lr", "Cuadrante inferior derecho"),
            ("ll", "Cuadrante inferior izquierdo"),
        ],
        string="Cuadrante",
    )

    diagnosis_text = fields.Text(string="Diagnóstico (texto)")
    odontogram_line_id = fields.Many2one(
        "df.patient.odontogram.line",
        string="Línea odontograma",
        ondelete="set null",
    )

    qty = fields.Float(string="Cantidad", default=1.0, required=True)
    currency_id = fields.Many2one(
        related="plan_id.currency_id",
        store=True,
        readonly=True,
    )
    estimated_unit_price = fields.Monetary(string="Precio unitario estimado", currency_field="currency_id")
    estimated_subtotal = fields.Monetary(
        string="Subtotal estimado",
        compute="_compute_estimated_subtotal",
        store=True,
        currency_field="currency_id",
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("proposed", "Propuesto"),
            ("accepted", "Aceptado"),
            ("rejected", "Rechazado"),
            ("planned", "Planificado"),
            ("in_progress", "En curso"),
            ("completed", "Completado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado línea",
        default="draft",
        required=True,
    )

    is_accepted = fields.Boolean(string="Aceptado por paciente")
    accepted_date = fields.Datetime(string="Fecha aceptación")

    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo",
        domain=[("share", "=", False)],
    )
    notes = fields.Text(string="Notas")

    @api.depends("qty", "estimated_unit_price")
    def _compute_estimated_subtotal(self):
        for rec in self:
            rec.estimated_subtotal = (rec.qty or 0.0) * (rec.estimated_unit_price or 0.0)

    @api.constrains("qty")
    def _check_qty(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_("La cantidad debe ser mayor que cero."))

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_plan_computed()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._invalidate_plan_computed()
        return lines

    def unlink(self):
        plans = self.mapped("plan_id")
        res = super().unlink()
        plans.invalidate_recordset(
            [
                "estimated_amount",
                "accepted_amount",
                "executed_amount",
                "progress_percent",
                "accepted_line_count",
                "completed_line_count",
            ]
        )
        return res

    def _invalidate_plan_computed(self):
        self.mapped("plan_id").invalidate_recordset(
            [
                "estimated_amount",
                "accepted_amount",
                "executed_amount",
                "progress_percent",
                "accepted_line_count",
                "completed_line_count",
            ]
        )
