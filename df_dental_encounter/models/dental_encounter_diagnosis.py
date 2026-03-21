# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalEncounterDiagnosis(models.Model):
    _name = "df.dental.encounter.diagnosis"
    _description = "Diagnóstico de encuentro dental"
    _order = "encounter_id, sequence, id"

    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    code = fields.Char(string="Código")
    name = fields.Char(string="Descripción", required=True)
    diagnosis_type = fields.Selection(
        [
            ("presumptive", "Presuntivo"),
            ("definitive", "Definitivo"),
        ],
        string="Tipo",
        default="presumptive",
        required=True,
    )
    tooth_code = fields.Char(string="Pieza / código dental")
    notes = fields.Text(string="Notas")
