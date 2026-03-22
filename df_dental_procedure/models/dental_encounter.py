# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class DentalEncounter(models.Model):
    _inherit = "df.dental.encounter"

    suite_procedure_ids = fields.One2many(
        "df.dental.procedure",
        "encounter_id",
        string="Procedimientos ejecutados (suite)",
    )
    suite_procedure_count = fields.Integer(
        string="Nº procedimientos suite",
        compute="_compute_suite_procedure_count",
    )

    @api.depends("suite_procedure_ids")
    def _compute_suite_procedure_count(self):
        for rec in self:
            rec.suite_procedure_count = len(rec.suite_procedure_ids)

    def action_create_suite_procedure(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Nuevo procedimiento"),
            "res_model": "df.dental.procedure",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_patient_id": self.patient_id.id,
                "default_encounter_id": self.id,
                "default_dentist_id": self.dentist_id.id,
                "default_company_id": self.company_id.id,
                "default_currency_id": self.env.company.currency_id.id,
                "default_state": "draft",
            },
        }

    def action_open_suite_procedures(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Procedimientos"),
            "res_model": "df.dental.procedure",
            "view_mode": "tree,form",
            "domain": [("encounter_id", "=", self.id)],
            "context": {
                "default_encounter_id": self.id,
                "default_patient_id": self.patient_id.id,
                "default_dentist_id": self.dentist_id.id,
            },
        }
