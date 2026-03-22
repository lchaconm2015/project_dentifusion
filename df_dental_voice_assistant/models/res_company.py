# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    voice_assistant_enabled = fields.Boolean(string="Asistente de voz habilitado", default=True)
    voice_auto_confirm = fields.Boolean(
        string="Confirmar automáticamente eventos de voz",
        default=True,
        help="Si está desactivado, los eventos quedan pendientes hasta confirmación manual.",
    )
    voice_store_audio = fields.Boolean(
        string="Permitir almacenar adjuntos de audio",
        default=True,
    )
    voice_default_channel = fields.Selection(
        [
            ("alexa", "Alexa"),
            ("web", "Web clínica"),
            ("mobile", "Móvil"),
            ("api", "API"),
            ("openclaw", "OpenClaw"),
            ("other", "Otro"),
        ],
        string="Canal de voz por defecto",
        default="web",
    )
    voice_require_encounter = fields.Boolean(
        string="Exigir encuentro para ejecutar acciones clínicas",
        default=True,
    )
    voice_allow_plan_creation = fields.Boolean(
        string="Permitir crear líneas de plan por voz",
        default=True,
    )
    voice_allow_procedure_creation = fields.Boolean(
        string="Permitir crear procedimientos por voz",
        default=True,
    )
