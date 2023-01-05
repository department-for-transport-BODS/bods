import enum


@enum.unique
class AccountType(enum.IntEnum):
    site_admin = 1
    org_admin = 2
    org_staff = 3
    developer = 4
    agent_user = 5


SiteAdminType = AccountType.site_admin.value
OrgAdminType = AccountType.org_admin.value
OrgStaffType = AccountType.org_staff.value
DeveloperType = AccountType.developer.value
AgentUserType = AccountType.agent_user.value

DATASET_MANAGE_TABLE_PAGINATE_BY = 10
