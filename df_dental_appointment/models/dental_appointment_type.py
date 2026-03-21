# -*- coding: utf-8 -*-
from odoo import fields, models


class DentalAppointmentType(models.Model):
    _name = "df.dental.appointment.type"
    _description = "Tipo de cita (plantilla)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True, translate=True)
    default_duration_minutes = fields.Integer(
        string="Duración sugerida (min)",
        default=30,
        required=True,
    )
    specialty_id = fields.Many2one("df.dental.specialty", string="Especialidad por defecto")
    color = fields.Integer(string="Color índice")
    active = fields.Boolean(default=True)
