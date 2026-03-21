# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalRoom(models.Model):
    _name = "df.dental.room"
    _description = "Consultorio"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    location = fields.Char(string="Ubicación")
    active = fields.Boolean(default=True)
