{
    "name": "DF Patient Odontogram",
    "version": "16.0.1.0.1",
    "summary": "Odontograma interactivo para pacientes",
    "category": "Healthcare_11",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": ["web", "mail", "df_patient_registration"],
    "data": [
        "security/ir.model.access.csv",
        "views/patient_odontogram_views.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "df_patient_odontogram/static/src/xml/odontogram_field.xml",
            "df_patient_odontogram/static/src/scss/odontogram.scss",
            "df_patient_odontogram/static/src/js/odontogram_field.js"
        ]
    },
    "installable": True,
    "application": False
}
