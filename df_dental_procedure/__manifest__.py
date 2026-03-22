{
    "name": "DF Dental Procedure",
    "version": "16.0.1.0.0",
    "summary": "Procedimientos clínicos odontológicos ejecutados",
    "category": "Healthcare",
    "author": "LICSYST",
    "website": "https://www.licsyst.com",
    "license": "LGPL-3",
    "depends": [
        "df_dental_treatment_plan",
    ],
    "data": [
        "security/dental_procedure_security.xml",
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "views/dental_procedure_views.xml",
        "views/dental_treatment_plan_views.xml",
        "views/dental_encounter_views.xml",
        "views/dental_procedure_menus.xml",
    ],
    "installable": True,
    "application": False,
}
