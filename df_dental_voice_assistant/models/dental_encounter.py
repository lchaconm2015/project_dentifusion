# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalEncounter(models.Model):
    _inherit = "df.dental.encounter"

    voice_session_ids = fields.One2many(
        "df.dental.voice.session",
        "encounter_id",
        string="Sesiones de voz",
    )
    voice_session_count = fields.Integer(
        string="Sesiones voz",
        compute="_compute_voice_session_count",
    )

    @api.depends("voice_session_ids")
    def _compute_voice_session_count(self):
        for rec in self:
            rec.voice_session_count = len(rec.voice_session_ids)

    def action_start_voice_session(self):
        self.ensure_one()
        comp = self.company_id
        if hasattr(comp, "voice_assistant_enabled") and not comp.voice_assistant_enabled:
            raise UserError(_("El asistente de voz está deshabilitado para esta compañía."))
        Session = self.env["df.dental.voice.session"]
        default_channel = "web"
        if hasattr(comp, "voice_default_channel") and comp.voice_default_channel:
            default_channel = comp.voice_default_channel
        session = Session.create(
            {
                "patient_id": self.patient_id.id,
                "encounter_id": self.id,
                "appointment_id": self.appointment_id.id,
                "dentist_id": self.dentist_id.id,
                "assistant_id": self.assistant_id.id,
                "company_id": self.company_id.id,
                "channel": default_channel,
                "state": "active",
                "start_datetime": fields.Datetime.now(),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Sesión de voz"),
            "res_model": "df.dental.voice.session",
            "view_mode": "form",
            "res_id": session.id,
            "target": "current",
        }

    def action_open_voice_sessions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sesiones de voz"),
            "res_model": "df.dental.voice.session",
            "view_mode": "tree,form",
            "domain": [("encounter_id", "=", self.id)],
            "context": {
                "default_encounter_id": self.id,
                "default_patient_id": self.patient_id.id,
                "default_dentist_id": self.dentist_id.id,
                "default_company_id": self.company_id.id,
            },
        }
