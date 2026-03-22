# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalVoiceCommandRule(models.Model):
    _name = "df.dental.voice.command.rule"
    _description = "Regla de mapeo texto → intención (voz)"
    _order = "priority desc, sequence, id"

    name = fields.Char(string="Descripción", required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    trigger_text = fields.Char(
        string="Texto disparador",
        required=True,
        help="Fragmento que debe aparecer en el texto normalizado (minúsculas).",
    )
    intent = fields.Selection(
        [
            ("open_session", "Abrir sesión"),
            ("close_session", "Cerrar sesión"),
            ("add_clinical_note", "Nota clínica"),
            ("add_odontogram_finding", "Hallazgo odontograma"),
            ("add_procedure", "Procedimiento"),
            ("add_treatment_plan_line", "Línea plan tratamiento"),
            ("update_encounter", "Actualizar encuentro"),
            ("unknown", "Desconocido"),
        ],
        string="Intención",
        required=True,
    )
    priority = fields.Integer(string="Prioridad", default=10)
    notes = fields.Text(string="Notas internas")
