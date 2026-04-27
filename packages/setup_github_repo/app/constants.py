"""Static constants for AWS profiles, app IDs, and target service hostnames."""

AWS_PROFILE_BY_ENV: dict[str, str] = {
    "dev": "prescription-dev",
    "qa": "prescription-qa",
    "ref": "prescription-ref",
    "int": "prescription-int",
    "prod": "prescription-prod-readonly",
    "recovery": "prescription-recovery",
}

AUTOMERGE_APP_ID = "420347"
CREATE_PULL_REQUEST_APP_ID = "3182106"

TARGET_SPINE_SERVERS: dict[str, str] = {
    "dev": "msg.veit07.devspineservices.nhs.uk",
    "int": "msg.intspineservices.nhs.uk",
    "prod": "prescriptions.spineservices.nhs.uk",
    "qa": "msg.intspineservices.nhs.uk",
    "ref": "prescriptions.refspineservices.nhs.uk",
    "recovery": "msg.veit07.devspineservices.nhs.uk",
}

TARGET_SERVICE_SEARCH_SERVERS: dict[str, str] = {
    "dev": "int.api.service.nhs.uk",
    "int": "api.service.nhs.uk",
    "prod": "api.service.nhs.uk",
    "qa": "int.api.service.nhs.uk",
    "ref": "api.service.nhs.uk",
    "recovery": "api.service.nhs.uk",
}
