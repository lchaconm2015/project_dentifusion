from odoo import api, fields, models


class DfPatientRegistration(models.Model):
    _name = "df.patient.registration"
    _description = "Registro de Pacientes"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "id desc"

    display_name = fields.Char(
        string="Paciente",
        compute="_compute_display_name",
        store=True,
    )

    # A. Datos del establecimiento y usuario/paciente
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto relacionado",
        help="Contacto comercial / fiscal vinculado a este paciente.",
        ondelete="set null",
    )
    patient_photo = fields.Image(
        string="Foto del paciente",
        max_width=1024,
        max_height=1024,
    )
    identification = fields.Char(string="Cédula", tracking=True)
    address = fields.Char(string="Dirección")
    phone = fields.Char(string="Teléfono", tracking=True)
    institution_system = fields.Char(string="Institución del sistema", tracking=True)
    unicodigo = fields.Char(string="Unicódigo", tracking=True)
    health_establishment = fields.Char(string="Establecimiento de salud")
    unique_clinical_history_number = fields.Char(string="Número de historia clínica única")
    file_number = fields.Char(string="Número de archivo")
    sheet_number = fields.Char(string="No. hoja")

    first_lastname = fields.Char(string="Primer apellido", required=True, tracking=True)
    second_lastname = fields.Char(string="Segundo apellido")
    first_name = fields.Char(string="Primer nombre", required=True, tracking=True)
    second_name = fields.Char(string="Segundo nombre")

    sex = fields.Selection(
        [
            ("male", "Masculino"),
            ("female", "Femenino"),
            ("other", "Otro"),
        ],
        string="Sexo",
        tracking=True,
    )

    age = fields.Integer(string="Edad")
    age_condition = fields.Selection(
        [
            ("hours", "H"),
            ("days", "D"),
            ("months", "M"),
            ("years", "A"),
        ],
        string="Condición edad",
        default="years",
    )

    # B. Motivo de consulta
    consultation_reason = fields.Text(string="Motivo de consulta")
    pregnant = fields.Boolean(string="Embarazada")

    # C. Enfermedad actual
    current_illness = fields.Text(string="Enfermedad actual")

    # D. Antecedentes patológicos personales
    personal_no_refiere = fields.Boolean(string="No refiere")
    personal_antibiotic_allergy = fields.Boolean(string="Alergia antibiótico")
    personal_anesthesia_allergy = fields.Boolean(string="Alergia anestesia")
    personal_hemorrhages = fields.Boolean(string="Hemorragias")
    personal_hiv_aids = fields.Boolean(string="VIH / SIDA")
    personal_tuberculosis = fields.Boolean(string="Tuberculosis")
    personal_asthma = fields.Boolean(string="Asma")
    personal_diabetes = fields.Boolean(string="Diabetes")
    personal_hypertension = fields.Boolean(string="Hipertensión arterial")
    personal_heart_disease = fields.Boolean(string="Enfermedad cardíaca")
    personal_other = fields.Boolean(string="Otro")
    personal_background_notes = fields.Text(string="Observaciones antecedentes personales")
    personal_observaciones = fields.Text(string="Observaciones")

    # E. Antecedentes patológicos familiares
    family_no_refiere = fields.Boolean(string="No refiere")
    family_cardiopathy = fields.Boolean(string="Cardiopatía")
    family_hypertension = fields.Boolean(string="Hipertensión arterial")
    family_vascular_disease = fields.Boolean(string="Enf. C. Vascular")
    family_endocrine_metabolic = fields.Boolean(string="Endócrino metabólico")
    family_cancer = fields.Boolean(string="Cáncer")
    family_tuberculosis = fields.Boolean(string="Tuberculosis")
    family_mental_illness = fields.Boolean(string="Enf. mental")
    family_infectious_disease = fields.Boolean(string="Enf. infecciosa")
    family_malformation = fields.Boolean(string="Malformación")
    family_other = fields.Boolean(string="Otro")
    family_background_notes = fields.Text(string="Observaciones antecedentes familiares")
    family_observaciones = fields.Text(string="Observaciones")

    # F. Constantes vitales
    temperature = fields.Float(string="Temperatura °C", digits=(16, 2))
    pulse = fields.Integer(string="Pulso / min.")
    respiratory_rate = fields.Integer(string="Frecuencia respiratoria / min.")
    blood_pressure = fields.Char(string="Presión arterial (mmHg)")

    # G. Examen del sistema estomatognático
    exam_lips = fields.Text(string="Labios")
    exam_cheeks = fields.Text(string="Mejillas")
    exam_upper_jaw = fields.Text(string="Maxilar superior")
    exam_lower_jaw = fields.Text(string="Maxilar inferior")
    exam_tongue = fields.Text(string="Lengua")
    exam_palate = fields.Text(string="Paladar")
    exam_floor_of_mouth = fields.Text(string="Piso de la boca")
    exam_cheeks_inner = fields.Text(string="Carrillos")
    exam_salivary_glands = fields.Text(string="Glándulas salivales")
    exam_oropharynx = fields.Text(string="Oro faringe")
    exam_atm = fields.Text(string="A.T.M.")
    exam_ganglia = fields.Text(string="Ganglios")
    exam_others = fields.Text(string="Otros")
    affected_region_description = fields.Text(
        string="Descripción de la patología de la región afectada"
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activo"),
            ("archived", "Archivado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )
    partner_invoice_count = fields.Integer(string="Facturas", compute="_compute_partner_invoice_count")
    patient_image_attachment_ids = fields.Many2many(
        "ir.attachment",
        "df_patient_registration_image_attachment_rel",
        "patient_id",
        "attachment_id",
        string="Imágenes del paciente",
        help="Adjunta imágenes relacionadas a la historia clínica (fotografías, radiografías, etc.).",
    )
    treatment_line_ids = fields.One2many(
        "df.patient.registration.treatment.line",
        "patient_id",
        string="Tratamientos",
    )
    active = fields.Boolean(default=True)

    @api.depends("first_name", "second_name", "first_lastname", "second_lastname")
    def _compute_display_name(self):
        for rec in self:
            parts = [
                rec.first_name or "",
                rec.second_name or "",
                rec.first_lastname or "",
                rec.second_lastname or "",
            ]
            rec.display_name = " ".join([p for p in parts if p]).strip()

    # -------------------------------------------------------------------------
    # Sincronización con res.partner
    # -------------------------------------------------------------------------

    def _get_partner_base_vals(self):
        """Valores base para crear/actualizar el partner desde el paciente."""
        self.ensure_one()
        name = self.display_name or ""
        vals = {
            "name": name,
        }
        if self.identification:
            vals["vat"] = self.identification
        if self.address:
            vals["street"] = self.address
        if self.phone:
            vals["phone"] = self.phone
        return vals

    def _ensure_partner(self):
        """Crear o vincular automáticamente un partner para el paciente.

        Estrategia:
        - Si ya hay partner_id, no hace nada.
        - Si no hay, busca un partner por nombre exacto (display_name).
          - Si encuentra uno, lo vincula.
          - Si no encuentra, crea un partner nuevo con datos básicos.
        """
        for rec in self:
            if rec.partner_id:
                continue

            name = rec.display_name or ""
            if not name and not rec.identification:
                continue

            Partner = rec.env["res.partner"]

            # Buscar primero por identificación (evita duplicados)
            existing = False
            if rec.identification:
                existing = Partner.search([("vat", "=", rec.identification)], limit=1)

            # Si no hay por identificación, buscar por nombre exacto
            if not existing and name:
                existing = Partner.search([("name", "=", name)], limit=1)
            if existing:
                rec.partner_id = existing.id
                continue

            # Crear un nuevo partner con datos básicos
            partner_vals = rec._get_partner_base_vals()
            partner = Partner.create(partner_vals)
            rec.partner_id = partner.id

    @api.depends("partner_id")
    def _compute_partner_invoice_count(self):
        AccountMove = self.env.get("account.move")
        for rec in self:
            if not AccountMove or not rec.partner_id:
                rec.partner_invoice_count = 0
                continue
            rec.partner_invoice_count = AccountMove.search_count(
                [
                    ("partner_id", "=", rec.partner_id.id),
                    ("move_type", "in", ["out_invoice", "out_refund"]),
                    ("state", "!=", "cancel"),
                ]
            )

    @api.model
    def create(self, vals):
        records = super().create(vals)
        records._ensure_partner()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Sincronizar cambios básicos de nombre al partner vinculado
        sync_fields = {
            "first_name",
            "second_name",
            "first_lastname",
            "second_lastname",
            "identification",
            "address",
            "phone",
        }
        if sync_fields.intersection(vals.keys()):
            for rec in self.filtered("partner_id"):
                partner_vals = rec._get_partner_base_vals()
                rec.partner_id.write(
                    {
                        "name": partner_vals.get("name"),
                        "vat": partner_vals.get("vat") or rec.partner_id.vat,
                        "street": partner_vals.get("street") or rec.partner_id.street,
                    }
                )
        return res

    # -------------------------------------------------------------------------
    # Acciones smart buttons
    # -------------------------------------------------------------------------

    def action_open_partner(self):
        self.ensure_one()
        if not self.partner_id:
            return False
        action = self.env.ref("base.action_partner_form").read()[0]
        action["views"] = [(False, "form")]
        action["res_id"] = self.partner_id.id
        return action

    def action_open_partner_invoices(self):
        self.ensure_one()
        if not self.partner_id:
            return False
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        action["domain"] = [("partner_id", "=", self.partner_id.id)]
        ctx = dict(self.env.context, default_partner_id=self.partner_id.id)
        action["context"] = ctx
        return action

    # -------------------------------------------------------------------------
    # Acciones de estado
    # -------------------------------------------------------------------------

    def action_set_state_draft(self):
        self.write({"state": "draft", "active": True})
        return True

    def action_set_state_active(self):
        self.write({"state": "active", "active": True})
        return True

    def action_set_state_archived(self):
        # Mantiene trazabilidad con state y además archiva el registro (active=False)
        self.write({"state": "archived", "active": False})
        return True


class DfPatientRegistrationTreatmentLine(models.Model):
    _name = "df.patient.registration.treatment.line"
    _description = "Líneas de tratamiento del paciente"
    _order = "date desc, id desc"

    patient_id = fields.Many2one(
        "df.patient.registration",
        string="Paciente",
        required=True,
        ondelete="cascade",
        index=True,
    )
    session_number = fields.Char(string="No. sesión")
    date = fields.Date(string="Fecha")
    diagnosis_complications = fields.Text(string="Diagnósticos y complicaciones")
    procedures = fields.Text(string="Procedimientos")
    prescriptions = fields.Text(string="Prescripciones")
    cost = fields = fields.Text(string="Costo")
