# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalSpecialty(models.Model):
    _name = "df.dental.specialty"
    _description = "Especialidad dental"
    _order = "name"

    name = fields.Char(string="Nombre", required=True, translate=True)
    code = fields.Char(string="Código")
    active = fields.Boolean(default=True)
