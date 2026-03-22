# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class DentalEncounter(models.Model):
    _inherit = "df.dental.encounter"

    treatment_plan_ids = fields.One2many(
        "df.dental.treatment.plan",
        "encounter_id",
        string="Planes de tratamiento",
    )
    treatment_plan_count = fields.Integer(
        string="Nº planes",
        compute="_compute_treatment_plan_count",
    )

    @api.depends("treatment_plan_ids")
    def _compute_treatment_plan_count(self):
        for rec in self:
            rec.treatment_plan_count = len(rec.treatment_plan_ids)

    def action_create_treatment_plan(self):
        self.ensure_one()
        ctx = {
            "default_patient_id": self.patient_id.id,
            "default_encounter_id": self.id,
            "default_dentist_id": self.dentist_id.id,
            "default_chief_complaint": self.chief_complaint,
            "default_clinical_summary": self.closure_summary or self.assessment_note,
            "default_plan_date": fields.Date.context_today(self),
        }
        return {
            "type": "ir.actions.act_window",
            "name": _("Nuevo plan de tratamiento"),
            "res_model": "df.dental.treatment.plan",
            "view_mode": "form",
            "target": "current",
            "context": ctx,
        }

    def action_open_treatment_plans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Planes de tratamiento"),
            "res_model": "df.dental.treatment.plan",
            "view_mode": "tree,form",
            "domain": [("encounter_id", "=", self.id)],
            "context": {"default_encounter_id": self.id, "default_patient_id": self.patient_id.id},
        }
