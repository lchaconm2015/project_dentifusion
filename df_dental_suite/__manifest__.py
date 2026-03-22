{
    "name": "DF Dental Suite (menú unificado)",
    "version": "16.0.1.0.0",
    "summary": "Punto de acceso único y menús agrupados para la suite odontológica",
    "category": "Healthcare",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": [
        "df_dental_procedure",
        "df_patient_registration",
    ],
    "data": [
        "security/dental_suite_menu_security.xml",
        "views/dental_suite_menus.xml",
    ],
    "installable": True,
    "application": False,
}
