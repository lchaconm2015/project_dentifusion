from odoo import fields, models


class DentalVoiceSessionLine(models.Model):
    _name = "dental.voice.session.line"
    _description = "Líneas de hallazgos odontológicos (voz / Alexa)"
    _order = "sequence, id"

    session_id = fields.Many2one(
        "dental.voice.session",
        string="Sesión",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)

    tooth_code = fields.Selection(
        [
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
            ("14", "14"),
            ("15", "15"),
            ("16", "16"),
            ("17", "17"),
            ("18", "18"),
            ("21", "21"),
            ("22", "22"),
            ("23", "23"),
            ("24", "24"),
            ("25", "25"),
            ("26", "26"),
            ("27", "27"),
            ("28", "28"),
            ("31", "31"),
            ("32", "32"),
            ("33", "33"),
            ("34", "34"),
            ("35", "35"),
            ("36", "36"),
            ("37", "37"),
            ("38", "38"),
            ("41", "41"),
            ("42", "42"),
            ("43", "43"),
            ("44", "44"),
            ("45", "45"),
            ("46", "46"),
            ("47", "47"),
            ("48", "48"),
        ],
        string="Pieza",
        required=True,
    )

    surface = fields.Selection(
        [
            ("oclusal", "Oclusal"),
            ("vestibular", "Vestibular"),
            ("mesial", "Mesial"),
            ("distal", "Distal"),
            ("lingual", "Lingual"),
            ("palatino", "Palatino"),
        ],
        string="Superficie",
    )

    finding = fields.Selection(
        [
            ("ausente", "Ausente"),
            ("caries", "Caries"),
            ("fractura", "Fractura"),
            ("resina", "Resina"),
            ("endodoncia", "Endodoncia"),
            ("corona", "Corona"),
            ("sellante", "Sellante"),
            ("movilidad", "Movilidad"),
        ],
        string="Hallazgo",
        required=True,
    )

    raw_payload = fields.Text(string="Payload crudo Alexa")
