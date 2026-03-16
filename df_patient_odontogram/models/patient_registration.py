from odoo import api, fields, models, _


class DfPatientRegistration(models.Model):
    _inherit = "df.patient.registration"

    odontogram_count = fields.Integer(
        string="Odontogramas",
        compute="_compute_odontogram_count",
    )

    def _compute_odontogram_count(self):
        grouped = self.env["df.patient.odontogram"].read_group(
            [("patient_id", "in", self.ids)],
            ["patient_id"],
            ["patient_id"],
        )
        mapped_data = {item["patient_id"][0]: item["patient_id_count"] for item in grouped}
        for rec in self:
            rec.odontogram_count = mapped_data.get(rec.id, 0)

    def action_open_odontogram(self):
        self.ensure_one()
        odontogram = self.env["df.patient.odontogram"].search([("patient_id", "=", self.id)], limit=1)
        if not odontogram:
            odontogram = self.env["df.patient.odontogram"].create({"patient_id": self.id})
            odontogram.action_sync_lines_from_chart()

        action = self.env.ref("df_patient_odontogram.action_df_patient_odontogram").read()[0]
        action["views"] = [(self.env.ref("df_patient_odontogram.view_df_patient_odontogram_form").id, "form")]
        action["res_id"] = odontogram.id
        return action
