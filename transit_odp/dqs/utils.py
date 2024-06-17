from django.conf import settings

AWS_ENVIRONMENT = settings.AWS_ENVIRONMENT.lower()


def get_checks_data(checks_list: list) -> list:
    """Returns checks data with queue names prefixed with environment name"""

    return [
        {**check, "queue_name": f"dqs-{AWS_ENVIRONMENT}-{check['queue_name']}"}
        for check in checks_list
    ]
