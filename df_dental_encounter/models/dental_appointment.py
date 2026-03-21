# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


_APPOINTMENT_TO_CONSULTATION = {
    "first_time": "first_time",
    "follow_up": "follow_up",
    "emergency": "emergency",
    "evaluation": "evaluation",
    "treatment": "procedure",
    "hygiene": "control",
    "surgery": "procedure",
    "orthodontics": "procedure",
    "administrative": "control",
}


class DentalAppointment(models.Model):
    _inherit = "df.dental.appointment"

    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Atención clínica",
        copy=False,
        ondelete="set null",
    )
    has_encounter = fields.Boolean(
        string="Tiene atención",
        compute="_compute_has_encounter",
        store=True,
    )

    @api.depends("encounter_id")
    def _compute_has_encounter(self):
        for rec in self:
            rec.has_encounter = bool(rec.encounter_id)

    def _map_appointment_type_to_consultation(self):
        self.ensure_one()
        return _APPOINTMENT_TO_CONSULTATION.get(self.appointment_type, "follow_up")

    def _prepare_encounter_vals(self):
        self.ensure_one()
        state = "in_progress" if self.state in ("checked_in", "in_progress") else "draft"
        return {
            "patient_id": self.patient_id.id,
            "appointment_id": self.id,
            "dentist_id": self.dentist_id.id,
            "assistant_id": self.assistant_id.id if self.assistant_id else False,
            "company_id": self.company_id.id,
            "date_start": self.start_datetime,
            "specialty_id": self.specialty_id.id if self.specialty_id else False,
            "consultation_type": self._map_appointment_type_to_consultation(),
            "state": state,
            "chief_complaint": self.notes or False,
        }

    def action_create_encounter(self):
        Encounter = self.env["df.dental.encounter"]
        for rec in self:
            if rec.encounter_id:
                raise UserError(_("Esta cita ya tiene una atención vinculada."))
            if rec.state in ("cancelled", "no_show", "draft", "done"):
                raise UserError(_("La cita debe estar activa (confirmada o en curso) para crear la atención clínica."))
            vals = rec._prepare_encounter_vals()
            encounter = Encounter.create(vals)
            rec.encounter_id = encounter.id
        return True

    def action_open_encounter(self):
        self.ensure_one()
        if not self.encounter_id:
            raise UserError(_("No hay atención vinculada."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Atención clínica"),
            "res_model": "df.dental.encounter",
            "view_mode": "form",
            "res_id": self.encounter_id.id,
        }
