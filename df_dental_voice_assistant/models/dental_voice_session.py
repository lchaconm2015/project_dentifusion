# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalVoiceSession(models.Model):
    _name = "df.dental.voice.session"
    _description = "Sesión de captura clínica por voz"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    patient_id = fields.Many2one(
        "df.patient.registration",
        string="Paciente",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    appointment_id = fields.Many2one(
        "df.dental.appointment",
        string="Cita",
        ondelete="set null",
        tracking=True,
    )
    encounter_id = fields.Many2one(
        "df.dental.encounter",
        string="Encuentro",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo",
        required=True,
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
        tracking=True,
    )
    assistant_id = fields.Many2one(
        "res.users",
        string="Asistente",
        domain=[("share", "=", False)],
    )
    channel = fields.Selection(
        [
            ("alexa", "Alexa"),
            ("web", "Web"),
            ("mobile", "Móvil"),
            ("api", "API"),
            ("openclaw", "OpenClaw"),
            ("other", "Otro"),
        ],
        string="Canal",
        default="web",
        required=True,
        tracking=True,
    )
    device_name = fields.Char(string="Dispositivo")
    external_session_ref = fields.Char(string="Referencia externa")
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("paused", "Pausada"),
            ("completed", "Completada"),
            ("cancelled", "Cancelada"),
            ("error", "Error"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )
    start_datetime = fields.Datetime(string="Inicio")
    end_datetime = fields.Datetime(string="Fin")
    notes = fields.Text(string="Notas")
    active = fields.Boolean(default=True)

    event_ids = fields.One2many(
        "df.dental.voice.event",
        "session_id",
        string="Eventos",
    )
    event_count = fields.Integer(string="Eventos", compute="_compute_event_counters")
    processed_event_count = fields.Integer(string="Procesados", compute="_compute_event_counters")
    error_event_count = fields.Integer(string="Con error", compute="_compute_event_counters")

    @api.depends("event_ids", "event_ids.execution_status")
    def _compute_event_counters(self):
        for rec in self:
            ev = rec.event_ids
            rec.event_count = len(ev)
            rec.processed_event_count = len(
                ev.filtered(lambda e: e.execution_status == "processed")
            )
            rec.error_event_count = len(ev.filtered(lambda e: e.execution_status == "error"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nuevo")) in (False, _("Nuevo")):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("df.dental.voice.session") or _("Nuevo")
                )
        return super().create(vals_list)

    def action_start(self):
        for rec in self:
            if rec.state not in ("draft", "paused"):
                raise UserError(_("Solo puede iniciar una sesión en borrador o pausada."))
            rec.write(
                {
                    "state": "active",
                    "start_datetime": fields.Datetime.now(),
                }
            )

    def action_pause(self):
        for rec in self:
            if rec.state != "active":
                raise UserError(_("Solo puede pausar una sesión activa."))
            rec.state = "paused"

    def action_resume(self):
        for rec in self:
            if rec.state != "paused":
                raise UserError(_("Solo puede reanudar una sesión pausada."))
            rec.state = "active"

    def action_complete(self):
        for rec in self:
            if rec.state not in ("active", "paused", "draft"):
                raise UserError(_("La sesión ya está cerrada o cancelada."))
            rec.write(
                {
                    "state": "completed",
                    "end_datetime": fields.Datetime.now(),
                }
            )

    def action_cancel(self):
        for rec in self:
            if rec.state == "completed":
                raise UserError(_("No puede cancelar una sesión ya completada."))
            rec.write(
                {
                    "state": "cancelled",
                    "end_datetime": fields.Datetime.now(),
                }
            )

    def action_open_events(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Eventos de voz"),
            "res_model": "df.dental.voice.event",
            "view_mode": "tree,form",
            "domain": [("session_id", "=", self.id)],
            "context": {"default_session_id": self.id},
        }

    def action_open_encounter(self):
        self.ensure_one()
        if not self.encounter_id:
            raise UserError(_("No hay encuentro vinculado."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Encuentro"),
            "res_model": "df.dental.encounter",
            "view_mode": "form",
            "res_id": self.encounter_id.id,
        }

    def register_text_command(self, text, source_type="text_command", auto_process=True):
        """API para canales externos: registra texto y opcionalmente procesa."""
        self.ensure_one()
        if self.state not in ("active", "draft"):
            raise UserError(_("La sesión no acepta comandos en el estado actual."))
        event = self.env["df.dental.voice.event"].create(
            {
                "session_id": self.id,
                "source_type": source_type,
                "raw_text": text,
                "channel": self.channel,
                "encounter_id": self.encounter_id.id,
            }
        )
        if auto_process:
            event.action_process()
        return event
