# -*- coding: utf-8 -*-
from odoo import _, fields, models


class DfPatientRegistration(models.Model):
    _inherit = "df.patient.registration"

    dental_treatment_plan_ids = fields.One2many(
        "df.dental.treatment.plan",
        "patient_id",
        string="Planes de tratamiento",
    )
    dental_treatment_plan_count = fields.Integer(
        string="Nº planes tratamiento",
        compute="_compute_dental_treatment_plan_count",
    )

    def _compute_dental_treatment_plan_count(self):
        grouped = self.env["df.dental.treatment.plan"].read_group(
            [("patient_id", "in", self.ids)],
            ["patient_id"],
            ["patient_id"],
        )
        mapped = {}
        for g in grouped:
            pt = g.get("patient_id")
            if not pt:
                continue
            mapped[pt[0]] = g.get("patient_id_count", g.get("__count", 0))
        for rec in self:
            rec.dental_treatment_plan_count = mapped.get(rec.id, 0)

    def action_open_dental_treatment_plans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Planes de tratamiento"),
            "res_model": "df.dental.treatment.plan",
            "view_mode": "tree,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {
                "default_patient_id": self.id,
                "default_partner_id": self.partner_id.id if self.partner_id else False,
            },
        }
