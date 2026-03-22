# -*- coding: utf-8 -*-
from odoo import fields, models


class DfPatientOdontogramLine(models.Model):
    _inherit = "df.patient.odontogram.line"

    clinical_capture_source = fields.Selection(
        [
            ("manual", "Manual"),
            ("voice", "Voz / asistente"),
            ("ai", "IA"),
            ("import", "Importación"),
        ],
        string="Origen de captura",
        default="manual",
        index=True,
    )
    last_voice_event_id = fields.Many2one(
        "df.dental.voice.event",
        string="Último evento de voz",
        ondelete="set null",
    )
