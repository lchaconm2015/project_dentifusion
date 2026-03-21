# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalEncounterProcedure(models.Model):
    _name = "df.dental.encounter.procedure"
    _description = "Procedimiento de encuentro dental"
    _order = "encounter_id, sequence, id"

    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    procedure_code = fields.Char(string="Código procedimiento")
    procedure_name = fields.Char(string="Procedimiento", required=True)
    tooth_code = fields.Char(string="Pieza")
    surface_codes = fields.Char(string="Superficies")
    status = fields.Selection(
        [
            ("planned", "Planificado"),
            ("performed", "Realizado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="planned",
        required=True,
    )
    notes = fields.Text(string="Notas")
    dentist_id = fields.Many2one(
        "res.users",
        string="Profesional",
        domain=[("share", "=", False)],
    )
