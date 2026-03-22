{
    "name": "DF Patient Registration",
    "version": "16.0.1.0.1",
    "summary": "Registro de pacientes para clínica",
    "category": "Healthcare_1_1_1_1_1_1_1",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "account"],
    "data": [
        "security/ir.model.access.csv",
        "reports/patient_registration_report.xml",
        "views/patient_registration_views.xml",
    ],
    "installable": True,
    "application": True,
}
