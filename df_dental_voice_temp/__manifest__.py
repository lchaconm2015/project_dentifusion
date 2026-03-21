{
    "name": "DF Dental Voice Temp",
    "version": "16.0.4.0.1",
    "summary": "Sesiones persistentes de odontograma por voz (Alexa)",
    "category": "Healthcare_test_2",
    "author": "lchaconm2015@gmail.com",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "df_patient_registration", "df_patient_odontogram"],
    "data": [
        "security/ir.model.access.csv",
        "views/dental_voice_session_views.xml",
    ],
    "installable": True,
    "application": False,
}

