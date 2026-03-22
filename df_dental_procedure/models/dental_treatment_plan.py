# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class DentalTreatmentPlan(models.Model):
    _inherit = "df.dental.treatment.plan"

    suite_procedure_ids = fields.One2many(
        "df.dental.procedure",
        "treatment_plan_id",
        string="Procedimientos (suite)",
    )

    def action_create_procedures(self):
        Procedure = self.env["df.dental.procedure"]
        created = self.env["df.dental.procedure"]
        for plan in self:
            if plan.state in ("cancelled", "rejected"):
                raise UserError(_("El plan no permite generar procedimientos."))
            encounter = plan.encounter_id
            for line in plan.line_ids.filtered(
                lambda l: l.is_accepted
                and l.state not in ("rejected", "cancelled", "completed")
            ):
                if line.procedure_ids.filtered(lambda p: p.state != "cancelled"):
                    continue
                vals = Procedure._prepare_from_plan_line_vals(line, encounter=encounter)
                proc = Procedure.create(vals)
                created |= proc
                if line.state in ("accepted", "proposed"):
                    line.state = "planned"
        if not created:
            raise UserError(_("No hay líneas aceptadas pendientes de procedimiento."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Procedimientos creados"),
            "res_model": "df.dental.procedure",
            "view_mode": "tree,form",
            "domain": [("id", "in", created.ids)],
        }

    def action_open_procedures(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Procedimientos del plan"),
            "res_model": "df.dental.procedure",
            "view_mode": "tree,form",
            "domain": [("treatment_plan_id", "=", self.id)],
            "context": {
                "default_treatment_plan_id": self.id,
                "default_patient_id": self.patient_id.id,
                "default_dentist_id": self.dentist_id.id,
                "default_company_id": self.company_id.id,
                "default_currency_id": self.currency_id.id,
            },
        }
