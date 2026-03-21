# -*- coding: utf-8 -*-
from odoo import _, fields, models


class DfPatientRegistration(models.Model):
    _inherit = "df.patient.registration"

    dental_encounter_ids = fields.One2many(
        "df.dental.encounter",
        "patient_id",
        string="Encuentros clínicos",
    )
    dental_encounter_count = fields.Integer(
        string="Nº atenciones",
        compute="_compute_dental_encounter_count",
    )

    def _compute_dental_encounter_count(self):
        grouped = self.env["df.dental.encounter"].read_group(
            [("patient_id", "in", self.ids)],
            ["patient_id"],
            ["patient_id"],
        )
        mapped = {}
        for g in grouped:
            pid_tuple = g.get("patient_id")
            if not pid_tuple:
                continue
            cnt = g.get("patient_id_count", g.get("__count", 0))
            mapped[pid_tuple[0]] = cnt
        for rec in self:
            rec.dental_encounter_count = mapped.get(rec.id, 0)

    def action_open_dental_encounters(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Atenciones"),
            "res_model": "df.dental.encounter",
            "view_mode": "tree,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id},
        }
