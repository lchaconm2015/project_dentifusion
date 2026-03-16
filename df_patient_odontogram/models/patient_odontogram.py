from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json


class DfPatientOdontogram(models.Model):
    _name = "df.patient.odontogram"
    _description = "Odontograma del Paciente"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _rec_name = "display_name"

    patient_id = fields.Many2one(
        "df.patient.registration",
        string="Paciente",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    display_name = fields.Char(
        string="Nombre",
        compute="_compute_display_name",
        store=True,
    )
    chart_data = fields.Text(
        string="Odontograma",
        default=lambda self: self._default_chart_data(),
        tracking=True,
    )
    line_ids = fields.One2many(
        "df.patient.odontogram.line",
        "odontogram_id",
        string="Detalle por pieza",
    )
    notes = fields.Text(string="Observaciones generales")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("unique_patient_odontogram", "unique(patient_id)", "Solo puede existir un odontograma por paciente."),
    ]

    @api.depends("patient_id.display_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = _("Odontograma - %s") % (rec.patient_id.display_name or "")

    @api.model
    def _default_chart_data(self):
        teeth = self._get_default_teeth()
        return json.dumps({"teeth": teeth}, ensure_ascii=False)

    @api.model
    def _get_default_teeth(self):
        permanent = [
            "18", "17", "16", "15", "14", "13", "12", "11",
            "21", "22", "23", "24", "25", "26", "27", "28",
            "48", "47", "46", "45", "44", "43", "42", "41",
            "31", "32", "33", "34", "35", "36", "37", "38",
        ]
        primary = [
            "55", "54", "53", "52", "51", "61", "62", "63", "64", "65",
            "85", "84", "83", "82", "81", "71", "72", "73", "74", "75",
        ]
        all_teeth = permanent + primary
        return {
            tooth_code: {
                "status": "healthy",
                "mobility": "",
                "recession": "",
                "notes": "",
            }
            for tooth_code in all_teeth
        }

    def action_generate_default_chart(self):
        for rec in self:
            rec.chart_data = rec._default_chart_data()
            rec.action_sync_lines_from_chart()

    def action_sync_lines_from_chart(self):
        for rec in self:
            payload = rec._safe_payload()
            for tooth_code, values in payload.get("teeth", {}).items():
                line = rec.line_ids.filtered(lambda l: l.tooth_code == tooth_code)[:1]
                vals = {
                    "tooth_code": tooth_code,
                    "status": values.get("status", "healthy"),
                    "mobility": values.get("mobility", ""),
                    "recession": values.get("recession", ""),
                    "notes": values.get("notes", ""),
                }
                if line:
                    line.write(vals)
                else:
                    vals["odontogram_id"] = rec.id
                    self.env["df.patient.odontogram.line"].create(vals)

            missing_lines = rec.line_ids.filtered(
                lambda l: l.tooth_code not in payload.get("teeth", {})
            )
            if missing_lines:
                missing_lines.unlink()

    def action_load_chart_from_lines(self):
        for rec in self:
            teeth = rec._get_default_teeth()
            for line in rec.line_ids:
                teeth[line.tooth_code] = {
                    "status": line.status or "healthy",
                    "mobility": line.mobility or "",
                    "recession": line.recession or "",
                    "notes": line.notes or "",
                }
            rec.chart_data = json.dumps({"teeth": teeth}, ensure_ascii=False)

    def _safe_payload(self):
        self.ensure_one()
        try:
            payload = json.loads(self.chart_data or "{}")
        except Exception:
            raise ValidationError(_("El campo del odontograma no contiene un JSON válido."))
        if not isinstance(payload, dict):
            raise ValidationError(_("La estructura del odontograma es inválida."))
        payload.setdefault("teeth", {})
        return payload


class DfPatientOdontogramLine(models.Model):
    _name = "df.patient.odontogram.line"
    _description = "Detalle de pieza dental"
    _order = "tooth_code"

    odontogram_id = fields.Many2one(
        "df.patient.odontogram",
        string="Odontograma",
        required=True,
        ondelete="cascade",
    )
    tooth_code = fields.Char(string="Pieza", required=True)
    status = fields.Selection(
        [
            ("healthy", "Sana"),
            ("treatment", "Tratamiento realizado"),
            ("pathology", "Patología actual"),
            ("missing", "Ausente"),
        ],
        string="Estado",
        default="healthy",
        required=True,
    )
    mobility = fields.Char(string="Movilidad")
    recession = fields.Char(string="Recesión")
    notes = fields.Text(string="Observaciones")

    _sql_constraints = [
        (
            "unique_tooth_per_odontogram",
            "unique(odontogram_id, tooth_code)",
            "La pieza dental ya existe en este odontograma.",
        )
    ]
