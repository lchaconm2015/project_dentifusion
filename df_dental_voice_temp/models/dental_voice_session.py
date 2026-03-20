from odoo import api, fields, models, _
from odoo.exceptions import UserError

FINDING_TO_STATUS = {
    "ausente": "missing",
    "caries": "pathology",
    "fractura": "pathology",
    "movilidad": "pathology",
    "resina": "treatment",
    "endodoncia": "treatment",
    "corona": "treatment",
    "sellante": "treatment",
}


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

    def _find_patient_registration(self):
        self.ensure_one()
        patient = self.env["df.patient.registration"]
        if self.partner_id:
            rec = patient.search([("partner_id", "=", self.partner_id.id)], limit=1)
            if rec:
                return rec
        return patient.search([("display_name", "ilike", self.patient_name)], limit=1)

    def action_apply_to_odontogram(self):
        """
        Aplica hallazgos de la sesión de voz al odontograma del paciente
        después de la revisión clínica del médico.
        """
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No hay hallazgos para aplicar al odontograma."))

        patient = self._find_patient_registration()
        if not patient:
            raise UserError(
                _(
                    "No se encontró ficha clínica del paciente para asociar el odontograma. "
                    "Verifique el paciente de la sesión."
                )
            )

        odontogram = self.env["df.patient.odontogram"].search(
            [("patient_id", "=", patient.id)], limit=1
        )
        if not odontogram:
            odontogram = self.env["df.patient.odontogram"].create({"patient_id": patient.id})
            odontogram.action_sync_lines_from_chart()

        for line in self.line_ids.sorted(key=lambda l: (l.sequence, l.id)):
            odo_line = odontogram.line_ids.filtered(lambda l: l.tooth_code == line.tooth_code)[:1]
            if not odo_line:
                odo_line = self.env["df.patient.odontogram.line"].create(
                    {
                        "odontogram_id": odontogram.id,
                        "tooth_code": line.tooth_code,
                        "status": "healthy",
                    }
                )

            status = FINDING_TO_STATUS.get(line.finding, "pathology")
            note_parts = [_("Fuente voz"), _("hallazgo: %s") % (line.finding or "")]
            if line.surface:
                note_parts.append(_("superficie: %s") % line.surface)
            note_txt = " | ".join(note_parts)
            existing_notes = (odo_line.notes or "").strip()
            combined_notes = f"{existing_notes}\n{note_txt}".strip() if existing_notes else note_txt

            vals = {"status": status, "notes": combined_notes}
            if line.finding == "movilidad" and not odo_line.mobility:
                vals["mobility"] = _("Reportada por voz")
            odo_line.write(vals)

        odontogram.action_load_chart_from_lines()
        return patient.action_open_odontogram()
