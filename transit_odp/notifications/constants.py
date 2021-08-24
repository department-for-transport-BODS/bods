from typing import Dict

TEMPLATE_LOOKUP: Dict[str, str] = {
    "VERIFY_EMAIL_ADDRESS": "notifications/verify_email_address.txt",
    "INVITE_USER": "notifications/invite_user.txt",
    "PASSWORD_RESET": "notifications/password_reset.txt",
    "OPERATOR_INVITE_ACCEPTED": "notifications/invite_accepted.txt",
    "OPERATOR_FEEDBACK": "notifications/leave_feedback.txt",
    "OPERATOR_DATA_DELETED": (
        "notifications/" "data_end_point_deleted_notifying_last_updated_user.txt"
    ),
    "OPERATOR_DELETER_DATA_DELETED": (
        "notifications/data_end_point_deleted_notifying_deleting_user.txt"
    ),
    "OPERATOR_DATA_ENDPOINT_UNREACHABLE_NOW_EXPIRING": (
        "notifications/data_end_point_unreachable_expiring.txt"
    ),
    "OPERATOR_DATA_ENDPOINT_NOW_REACHABLE": (
        "notifications/data_end_point_now_reachable.txt"
    ),
    "OPERATOR_DATA_ENDPOINT_UNREACHABLE": (
        "notifications/data_end_point_unreachable.txt"
    ),
    "OPERATOR_DATA_CHANGED": "notifications/data_end_point_changed.txt",
    "DEVELOPER_DATA_CHANGED": ("notifications/data_end_point_changed_developer.txt"),
    "AGENT_DATA_CHANGED": "notifications/data_end_point_changed_agent.txt",
    "OPERATOR_PUBLISH_LIVE": "notifications/data_end_point_published.txt",
    "OPERATOR_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
        "notifications/data_end_point_published_with_pti_violations.txt"
    ),
    "AGENT_PUBLISH_LIVE": "notifications/data_end_point_published_agent.txt",
    "AGENT_PUBLISH_LIVE_WITH_PTI_VIOLATIONS": (
        "notifications/data_end_point_published_with_pti_violations_agent.txt"
    ),
    "OPERATOR_PUBLISH_ERROR": ("notifications/data_end_point_error_publishing.txt"),
    "AGENT_PUBLISH_ERROR": ("notifications/data_end_point_error_publishing_agent.txt"),
    "OPERATOR_EXPIRED_NOTIFICATION": ("notifications/data_end_point_expired.txt"),
    "AGENT_EXPIRED_NOTIFICATION": ("notifications/data_end_point_expired_agent.txt"),
    "OPERATOR_AVL_ENDPOINT_UNREACHABLE": (
        "notifications/avl_end_point_unreachable.txt"
    ),
    "DEVELOPER_AVL_FEED_STATUS_NOTIFICATION": (
        "notifications/avl_feed_changed_developer.txt"
    ),
    "AGENT_INVITE_ACCEPTED": "notifications/agent_invite_accepted.txt",
    "AGENT_INVITE_EXISTING_ACCOUNT": (
        "notifications/agent_invite_existing_account.txt"
    ),
    "AGENT_INVITE_NEW_ACCOUNT": "notifications/agent_invite_no_account.txt",
    "AGENT_INVITE_REJECTED": "notifications/agent_invite_rejected.txt",
    "AGENT_LEAVES_ORGANISATION": "notifications/agent_leaves_operator.txt",
    "AGENT_NOC_CHANGED": "notifications/agent_noc_changed.txt",
    "AGENT_REMOVED_BY_OPERATOR": ("notifications/agent_operator_removes_agent.txt"),
    "OPERATOR_AGENT_INVITE_ACCEPTED": (
        "notifications/operator_agent_accepted_invite.txt"
    ),
    "OPERATOR_AGENT_LEAVES_ORGANISATION": ("notifications/operator_agent_leaves.txt"),
    "OPERATOR_AGENT_REJECTED_INVITE": (
        "notifications/operator_agent_rejected_invite.txt"
    ),
    "OPERATOR_AGENT_REMOVED": "notifications/operator_agent_removed.txt",
    "OPERATOR_NOC_CHANGED": "notifications/operator_noc_changed.txt",
    "REPORTS_AVAILABLE": "notifications/reports_are_available.txt",
    "AGENT_REPORTS_AVAILABLE": "notifications/reports_are_available_agent.txt",
    "DATASET_NO_LONGER_COMPLIANT": ("notifications/dataset_no_longer_compliant.txt"),
}
