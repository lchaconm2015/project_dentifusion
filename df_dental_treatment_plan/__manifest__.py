{
    "name": "DF Dental Treatment Plan",
    "version": "16.0.1.0.0",
    "summary": "Planes de tratamiento odontológico (propuesta terapéutica)",
    "category": "Healthcare",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": [
        "df_dental_encounter",
        "df_patient_odontogram",
    ],
    "data": [
        "security/dental_treatment_plan_security.xml",
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/dental_treatment_plan_views.xml",
        "views/dental_encounter_views.xml",
        "views/patient_registration_views.xml",
        "views/dental_treatment_plan_menus.xml",
    ],
    "installable": True,
    "application": False,
}
