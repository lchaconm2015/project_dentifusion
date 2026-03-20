from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalVoiceSession(models.Model):
    _name = "dental.voice.session"
    _description = "Sesión de odontograma por voz (Alexa)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Referencia", default=lambda self: _("Nueva sesión"), tracking=True)
    active = fields.Boolean(default=True)
    alexa_session_id = fields.Char(string="Alexa Session ID", index=True, tracking=True)
    patient_name = fields.Char(string="Paciente", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Paciente relacionado", tracking=True)
    started_at = fields.Datetime(string="Inicio", default=fields.Datetime.now, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_progress", "En progreso"),
            ("done", "Guardada"),
            ("cancel", "Cancelada"),
        ],
        default="draft",
        string="Estado",
        tracking=True,
    )

    line_ids = fields.One2many(
        "dental.voice.session.line",
        "session_id",
        string="Hallazgos",
    )

    summary_text = fields.Text(string="Resumen", compute="_compute_summary_text")

    @api.depends("line_ids", "line_ids.tooth_code", "line_ids.surface", "line_ids.finding")
    def _compute_summary_text(self):
        for rec in self:
            if not rec.line_ids:
                rec.summary_text = _("No hay hallazgos registrados.")
                continue

            lines = []
            for line in rec.line_ids.sorted(key=lambda l: (l.sequence, l.id)):
                if line.surface:
                    lines.append(
                        _(
                            "Pieza %(tooth)s, superficie %(surface)s, hallazgo %(finding)s"
                        )
                        % {
                            "tooth": line.tooth_code,
                            "surface": line.surface,
                            "finding": line.finding,
                        }
                    )
                else:
                    lines.append(
                        _("Pieza %(tooth)s, hallazgo %(finding)s")
                        % {"tooth": line.tooth_code, "finding": line.finding}
                    )
            rec.summary_text = "\n".join(lines)

    def action_start_session(self):
        for rec in self:
            rec.state = "in_progress"
        return True

    def action_register_finding(self, tooth_code, finding, surface=False, raw_payload=False):
        self.ensure_one()
        if self.state not in ("draft", "in_progress"):
            raise UserError(_("La sesión no está disponible para registrar hallazgos."))

        next_sequence = max(self.line_ids.mapped("sequence") or [0]) + 1

        self.env["dental.voice.session.line"].create(
            {
                "session_id": self.id,
                "sequence": next_sequence,
                "tooth_code": tooth_code,
                "surface": surface or False,
                "finding": finding,
                "raw_payload": raw_payload or False,
            }
        )

        if self.state == "draft":
            self.state = "in_progress"
        return True

    def action_delete_last(self):
        self.ensure_one()
        last_line = self.line_ids.sorted(key=lambda l: (l.sequence, l.id), reverse=True)[:1]
        if not last_line:
            raise UserError(_("No hay registros para borrar."))
        last_line.unlink()
        return True

    def action_save_session(self):
        """Marca la sesión como guardada (registro persistente; no se borra por vacuum)."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("No hay hallazgos para guardar."))

        self.state = "done"
        self.active = False
        return True
