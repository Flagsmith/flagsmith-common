VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"

# Maintain a list of permissions here
VIEW_PROJECT = "VIEW_PROJECT"
CREATE_ENVIRONMENT = "CREATE_ENVIRONMENT"
DELETE_FEATURE = "DELETE_FEATURE"
CREATE_FEATURE = "CREATE_FEATURE"
EDIT_FEATURE = "EDIT_FEATURE"
MANAGE_SEGMENTS = "MANAGE_SEGMENTS"
MANAGE_TAGS = "MANAGE_TAGS"

# Note that this does not impact change requests in an environment
MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS = "MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS"
APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS = "APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS"
CREATE_PROJECT_LEVEL_CHANGE_REQUESTS = "CREATE_PROJECT_LEVEL_CHANGE_REQUESTS"

TAG_SUPPORTED_PERMISSIONS = [DELETE_FEATURE]

PROJECT_PERMISSIONS = [
    (VIEW_PROJECT, "View permission for the given project."),
    (CREATE_ENVIRONMENT, "Ability to create an environment in the given project."),
    (DELETE_FEATURE, "Ability to delete features in the given project."),
    (CREATE_FEATURE, "Ability to create features in the given project."),
    (EDIT_FEATURE, "Ability to edit features in the given project."),
    (MANAGE_SEGMENTS, "Ability to manage segments in the given project."),
    (VIEW_AUDIT_LOG, "Allows the user to view the audit logs for this organisation."),
    (
        MANAGE_PROJECT_LEVEL_CHANGE_REQUESTS,
        "Ability to create, delete, and publish change requests associated with a project.",
    ),
    (
        APPROVE_PROJECT_LEVEL_CHANGE_REQUESTS,
        "Ability to approve project level change requests.",
    ),
    (
        CREATE_PROJECT_LEVEL_CHANGE_REQUESTS,
        "Ability to create project level change requests.",
    ),
    (MANAGE_TAGS, "Allows the user to manage tags in the given project."),
]
