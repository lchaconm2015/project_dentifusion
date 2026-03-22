# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class DentalAppointment(models.Model):
    _name = "df.dental.appointment"
    _description = "Cita odontológica"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"

    name = fields.Char(
        string="Referencia",
        compute="_compute_name",
        store=True,
        readonly=False,
        tracking=True,
    )
    sequence_code = fields.Char(
        string="Número",
        readonly=True,
        copy=False,
        default=lambda self: _("Nuevo"),
    )

    patient_id = fields.Many2one(
        "df.patient.registration",
        string="Paciente",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        tracking=True,
        ondelete="set null",
    )
    dentist_id = fields.Many2one(
        "res.users",
        string="Odontólogo",
        required=True,
        tracking=True,
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
    )
    assistant_id = fields.Many2one(
        "res.users",
        string="Asistente",
        domain=[("share", "=", False)],
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    start_datetime = fields.Datetime(string="Inicio", required=True, tracking=True)
    end_datetime = fields.Datetime(string="Fin", required=True, tracking=True)
    duration = fields.Float(
        string="Duración (min)",
        compute="_compute_duration",
        store=True,
    )
    appointment_date = fields.Date(
        string="Fecha",
        compute="_compute_appointment_date",
        store=True,
        index=True,
    )

    appointment_type = fields.Selection(
        [
            ("first_time", "Primera vez"),
            ("follow_up", "Control / seguimiento"),
            ("emergency", "Urgencia"),
            ("evaluation", "Evaluación"),
            ("treatment", "Tratamiento"),
            ("hygiene", "Higiene"),
            ("surgery", "Cirugía"),
            ("orthodontics", "Ortodoncia"),
            ("administrative", "Administrativo"),
        ],
        string="Tipo de cita",
        default="follow_up",
        required=True,
        tracking=True,
    )
    type_template_id = fields.Many2one(
        "df.dental.appointment.type",
        string="Plantilla de tipo",
        help="Opcional: aplica duración y especialidad sugeridas.",
    )
    specialty_id = fields.Many2one("df.dental.specialty", string="Especialidad")
    chair_id = fields.Many2one("df.dental.chair", string="Sillón / unidad")
    room_id = fields.Many2one("df.dental.room", string="Consultorio")

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmada"),
            ("checked_in", "Recepción"),
            ("in_progress", "En curso"),
            ("done", "Realizada"),
            ("no_show", "No asistió"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
    )
    # Tres columnas en Kanban; al arrastrar se actualiza state vía _inverse_kanban_lane
    kanban_lane = fields.Selection(
        [
            ("new", "Nuevas"),
            ("confirmed", "Confirmadas"),
            ("closed", "Canceladas / finalizadas"),
        ],
        string="Etapa (Kanban)",
        compute="_compute_kanban_lane",
        inverse="_inverse_kanban_lane",
        store=True,
        index=True,
    )

    notes = fields.Text(string="Notas de agenda")
    referred_by = fields.Char(string="Referido por")
    contact_phone = fields.Char(string="Teléfono contacto")
    contact_email = fields.Char(string="Correo contacto")

    checkin_datetime = fields.Datetime(string="Check-in")
    checkout_datetime = fields.Datetime(string="Check-out")
    attendance_status = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("attended", "Asistió"),
            ("absent", "Ausente"),
            ("cancelled", "Cancelada"),
        ],
        string="Asistencia",
        default="pending",
        tracking=True,
    )

    calendar_event_id = fields.Many2one(
        "calendar.event",
        string="Evento de calendario",
        copy=False,
        ondelete="set null",
    )

    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color calendario")

    cancel_reason = fields.Text(string="Motivo cancelación")

    @api.depends("patient_id", "start_datetime")
    def _compute_name(self):
        for rec in self:
            if rec.patient_id and rec.start_datetime:
                dt = fields.Datetime.context_timestamp(rec, rec.start_datetime)
                rec.name = _("Cita - %s - %s") % (
                    rec.patient_id.display_name,
                    dt.strftime("%Y-%m-%d %H:%M"),
                )
            elif rec.patient_id:
                rec.name = _("Cita - %s") % (rec.patient_id.display_name,)
            else:
                rec.name = _("Nueva cita")

    @api.depends("start_datetime", "end_datetime")
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                rec.duration = delta.total_seconds() / 60.0
            else:
                rec.duration = 0.0

    @api.depends("start_datetime")
    def _compute_appointment_date(self):
        for rec in self:
            if rec.start_datetime:
                rec.appointment_date = fields.Datetime.context_timestamp(
                    rec, rec.start_datetime
                ).date()
            else:
                rec.appointment_date = False

    @api.depends("state")
    def _compute_kanban_lane(self):
        for rec in self:
            if rec.state == "draft":
                rec.kanban_lane = "new"
            elif rec.state in ("done", "cancelled", "no_show"):
                rec.kanban_lane = "closed"
            else:
                rec.kanban_lane = "confirmed"

    def _kanban_lane_for_state(self, state):
        if state == "draft":
            return "new"
        if state in ("done", "cancelled", "no_show"):
            return "closed"
        return "confirmed"

    def _inverse_kanban_lane(self):
        """Sincroniza state al arrastrar tarjetas entre columnas del Kanban."""
        manager = "df_dental_appointment.group_df_dental_manager"
        for rec in self:
            lane = rec.kanban_lane
            current_lane = rec._kanban_lane_for_state(rec.state)
            if lane == current_lane:
                continue
            if lane == "new":
                if rec.state == "draft":
                    continue
                if not rec.env.user.has_group(manager):
                    raise UserError(
                        _(
                            "Solo un gestor dental puede mover la cita a «Nuevas» "
                            "(volver a borrador)."
                        )
                    )
                rec.write(
                    {
                        "state": "draft",
                        "checkin_datetime": False,
                        "checkout_datetime": False,
                        "attendance_status": "pending",
                    }
                )
            elif lane == "confirmed":
                if rec.state in ("confirmed", "checked_in", "in_progress"):
                    continue
                if rec.state == "done" and not rec.env.user.has_group(manager):
                    raise UserError(
                        _(
                            "Solo un gestor dental puede devolver una cita realizada "
                            "a «Confirmadas»."
                        )
                    )
                rec.write(
                    {
                        "state": "confirmed",
                        "checkin_datetime": False,
                        "checkout_datetime": False,
                        "attendance_status": "pending",
                    }
                )
            elif lane == "closed":
                if rec.state in ("done", "cancelled", "no_show"):
                    continue
                # En curso o ya en recepción → cerrar como realizada
                if rec.state in ("in_progress", "checked_in"):
                    rec.write(
                        {
                            "state": "done",
                            "checkout_datetime": fields.Datetime.now(),
                            "attendance_status": "attended",
                        }
                    )
                # Borrador o solo confirmada → interpretar como cancelación
                elif rec.state in ("draft", "confirmed"):
                    rec.write(
                        {"state": "cancelled", "attendance_status": "cancelled"}
                    )

    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        if self.patient_id:
            self.partner_id = self.patient_id.partner_id
            self.contact_phone = self.patient_id.phone or self.contact_phone
            # email might be on partner
            self.contact_email = (
                (self.patient_id.partner_id and self.patient_id.partner_id.email)
                or self.contact_email
            )

    @api.onchange("type_template_id")
    def _onchange_type_template_id(self):
        if self.type_template_id:
            if self.type_template_id.specialty_id:
                self.specialty_id = self.type_template_id.specialty_id
            if self.start_datetime and self.type_template_id.default_duration_minutes:
                self.end_datetime = self.start_datetime + timedelta(
                    minutes=self.type_template_id.default_duration_minutes
                )

    @api.onchange("start_datetime", "end_datetime")
    def _onchange_datetimes_duration(self):
        if self.start_datetime and self.end_datetime and self.end_datetime <= self.start_datetime:
            return {
                "warning": {
                    "title": _("Fechas inválidas"),
                    "message": _("La hora de fin debe ser posterior al inicio."),
                }
            }

    @api.constrains("start_datetime", "end_datetime")
    def _check_datetime_validity(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime and rec.end_datetime <= rec.start_datetime:
                raise ValidationError(_("La fecha/hora de fin debe ser posterior al inicio."))

    def _blocking_states(self):
        return ("confirmed", "checked_in", "in_progress")

    @api.constrains(
        "dentist_id",
        "start_datetime",
        "end_datetime",
        "state",
        "chair_id",
        "room_id",
    )
    def _check_overlaps(self):
        for rec in self:
            if rec.state not in self._blocking_states():
                continue
            if not (rec.dentist_id and rec.start_datetime and rec.end_datetime):
                continue
            domain = [
                ("id", "!=", rec.id),
                ("dentist_id", "=", rec.dentist_id.id),
                ("state", "in", self._blocking_states()),
                ("start_datetime", "<", rec.end_datetime),
                ("end_datetime", ">", rec.start_datetime),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _("El odontólogo ya tiene otra cita solapada en ese horario.")
                )
            if rec.chair_id:
                domain_chair = [
                    ("id", "!=", rec.id),
                    ("chair_id", "=", rec.chair_id.id),
                    ("state", "in", self._blocking_states()),
                    ("start_datetime", "<", rec.end_datetime),
                    ("end_datetime", ">", rec.start_datetime),
                ]
                if self.search_count(domain_chair):
                    raise ValidationError(
                        _("El sillón seleccionado ya está ocupado en ese horario.")
                    )
            if rec.room_id:
                domain_room = [
                    ("id", "!=", rec.id),
                    ("room_id", "=", rec.room_id.id),
                    ("state", "in", self._blocking_states()),
                    ("start_datetime", "<", rec.end_datetime),
                    ("end_datetime", ">", rec.start_datetime),
                ]
                if self.search_count(domain_room):
                    raise ValidationError(
                        _("El consultorio ya tiene otra cita solapada en ese horario.")
                    )

    def _sync_calendar_event_vals(self):
        self.ensure_one()
        partner_ids = []
        if self.partner_id:
            partner_ids = [(6, 0, [self.partner_id.id])]
        vals = {
            "name": self.name or _("Cita odontológica"),
            "start": self.start_datetime,
            "stop": self.end_datetime,
            "partner_ids": partner_ids,
            "user_id": self.dentist_id.id if self.dentist_id else False,
            "description": self.notes or "",
        }
        Event = self.env["calendar.event"]
        if "company_id" in Event._fields and self.company_id:
            vals["company_id"] = self.company_id.id
        return vals

    def _create_or_update_calendar_event(self):
        Event = self.env["calendar.event"].sudo()
        for rec in self:
            if not rec.start_datetime or not rec.end_datetime:
                continue
            vals = rec._sync_calendar_event_vals()
            if rec.calendar_event_id:
                rec.calendar_event_id.write(vals)
            else:
                event = Event.create(vals)
                rec.calendar_event_id = event.id

    def _unlink_calendar_event(self):
        for rec in self:
            if rec.calendar_event_id:
                rec.calendar_event_id.unlink()
                rec.calendar_event_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sequence_code", _("Nuevo")) in (False, _("Nuevo")):
                vals["sequence_code"] = self.env["ir.sequence"].next_by_code(
                    "df.dental.appointment"
                ) or _("Nuevo")
        records = super().create(vals_list)
        records.filtered(lambda r: r.state != "cancelled")._create_or_update_calendar_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            "name",
            "start_datetime",
            "end_datetime",
            "dentist_id",
            "partner_id",
            "notes",
            "state",
        }
        if sync_fields & set(vals):
            todo = self.filtered(lambda r: r.state != "cancelled")
            todo._create_or_update_calendar_event()
        if vals.get("state") == "cancelled":
            self.filtered("calendar_event_id")._unlink_calendar_event()
        return res

    def unlink(self):
        self._unlink_calendar_event()
        return super().unlink()

    # ---- State actions (encounter actions added by df_dental_encounter) ----

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Solo borradores pueden confirmarse."))
            rec.state = "confirmed"
            rec.attendance_status = "pending"

    def action_check_in(self):
        for rec in self:
            if rec.state not in ("confirmed", "draft"):
                raise UserError(_("Estado no válido para recepción."))
            rec.write(
                {
                    "state": "checked_in",
                    "checkin_datetime": fields.Datetime.now(),
                    "attendance_status": "attended",
                }
            )

    def action_start(self):
        for rec in self:
            if rec.state not in ("confirmed", "checked_in"):
                raise UserError(_("Debe confirmar o registrar recepción antes de iniciar."))
            rec.state = "in_progress"

    def action_mark_done(self):
        for rec in self:
            if rec.state not in ("in_progress", "checked_in", "confirmed"):
                raise UserError(_("No puede cerrar esta cita desde el estado actual."))
            rec.write(
                {
                    "state": "done",
                    "checkout_datetime": fields.Datetime.now(),
                    "attendance_status": "attended",
                }
            )

    def action_no_show(self):
        for rec in self:
            if rec.state in ("done", "cancelled", "no_show"):
                raise UserError(_("Esta cita ya está cerrada o cancelada."))
            rec.write(
                {
                    "state": "no_show",
                    "attendance_status": "absent",
                }
            )

    def action_cancel(self):
        for rec in self:
            if rec.state in ("done", "cancelled"):
                raise UserError(_("La cita ya está finalizada o cancelada."))
            rec.state = "cancelled"
            rec.attendance_status = "cancelled"

    def action_reset_draft(self):
        if not self.env.user.has_group("df_dental_appointment.group_df_dental_manager"):
            raise UserError(_("Solo un gestor puede devolver citas a borrador."))
        for rec in self:
            rec.write(
                {
                    "state": "draft",
                    "checkin_datetime": False,
                    "checkout_datetime": False,
                    "attendance_status": "pending",
                }
            )
        self._create_or_update_calendar_event()
