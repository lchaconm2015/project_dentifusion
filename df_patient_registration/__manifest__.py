{
    "name": "DF Patient Registration",
    "version": "16.0.1.0.0",
    "summary": "Registro de pacientes para clínica",
    "category": "Healthcare",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/patient_registration_views.xml",
    ],
    "installable": True,
    "application": True,
}
