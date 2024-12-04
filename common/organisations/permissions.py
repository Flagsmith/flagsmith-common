CREATE_PROJECT = "CREATE_PROJECT"
MANAGE_USER_GROUPS = "MANAGE_USER_GROUPS"

ORGANISATION_PERMISSIONS = (
    (CREATE_PROJECT, "Allows the user to create projects in this organisation."),
    (
        MANAGE_USER_GROUPS,
        "Allows the user to manage the groups in the organisation and their members.",
    ),
)
