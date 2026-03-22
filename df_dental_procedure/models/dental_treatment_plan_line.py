# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DentalTreatmentPlanLine(models.Model):
    _inherit = "df.dental.treatment.plan.line"

    procedure_ids = fields.One2many(
        "df.dental.procedure",
        "treatment_plan_line_id",
        string="Procedimientos ejecutados",
    )
    procedure_count = fields.Integer(
        string="Nº procedimientos",
        compute="_compute_procedure_stats",
        store=True,
    )
    completed_procedure_count = fields.Integer(
        string="Procedimientos realizados",
        compute="_compute_procedure_stats",
        store=True,
    )
    line_progress_percent = fields.Float(
        string="Avance línea (%)",
        compute="_compute_procedure_stats",
        store=True,
        digits=(16, 2),
    )

    @api.depends("procedure_ids", "procedure_ids.state")
    def _compute_procedure_stats(self):
        for rec in self:
            procs = rec.procedure_ids.filtered(lambda p: p.state != "cancelled")
            rec.procedure_count = len(procs)
            done = len(procs.filtered(lambda p: p.state == "performed"))
            rec.completed_procedure_count = done
            if procs:
                rec.line_progress_percent = (done / len(procs)) * 100.0
            else:
                rec.line_progress_percent = 0.0

    def _refresh_from_procedures(self):
        for rec in self:
            procs = rec.procedure_ids.filtered(lambda p: p.state != "cancelled")
            if not procs:
                continue
            if all(p.state == "performed" for p in procs):
                if rec.state not in ("cancelled", "rejected"):
                    rec.state = "completed"
            elif any(p.state == "performed" for p in procs) or any(
                p.state in ("in_progress", "ready") for p in procs
            ):
                if rec.state in ("accepted", "planned", "proposed"):
                    rec.state = "in_progress"
