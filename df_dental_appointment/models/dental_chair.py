# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalChair(models.Model):
    _name = "df.dental.chair"
    _description = "Sillón / unidad odontológica"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    room_id = fields.Many2one("df.dental.room", string="Consultorio")
    active = fields.Boolean(default=True)
