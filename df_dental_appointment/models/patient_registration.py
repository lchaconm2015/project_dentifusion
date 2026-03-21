# -*- coding: utf-8 -*-
from odoo import _, fields, models


class DfPatientRegistration(models.Model):
    _inherit = "df.patient.registration"

    dental_appointment_ids = fields.One2many(
        "df.dental.appointment",
        "patient_id",
        string="Citas odontológicas",
    )
    dental_appointment_count = fields.Integer(
        string="Nº citas",
        compute="_compute_dental_appointment_count",
    )

    def _compute_dental_appointment_count(self):
        grouped = self.env["df.dental.appointment"].read_group(
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
            rec.dental_appointment_count = mapped.get(rec.id, 0)

    def action_open_dental_appointments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Citas"),
            "res_model": "df.dental.appointment",
            "view_mode": "tree,form,calendar",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id, "default_partner_id": self.partner_id.id},
        }
