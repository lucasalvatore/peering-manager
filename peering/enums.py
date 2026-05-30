from utils.enums import ChoiceSet


class BGPGroupStatus(ChoiceSet):
    ENABLED = "enabled"
    PRE_MAINTENANCE = "pre-maintenance"
    MAINTENANCE = "maintenance"
    POST_MAINTENANCE = "post-maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (PRE_MAINTENANCE, "Pre-maintenance", "warning"),
        (MAINTENANCE, "Maintenance", "warning"),
        (POST_MAINTENANCE, "Post-maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )


class BGPSessionStatus(ChoiceSet):
    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    ENABLED = "enabled"
    PRE_MAINTENANCE = "pre-maintenance"
    MAINTENANCE = "maintenance"
    POST_MAINTENANCE = "post-maintenance"
    DISABLED = "disabled"
    DECOMMISSIONING = "decommissioning"
    DECOMMISSIONED = "decommissioned"

    CHOICES = (
        (REQUESTED, "Requested", "info"),
        (PROVISIONING, "Provisioning", "secondary"),
        (ENABLED, "Enabled", "success"),
        (PRE_MAINTENANCE, "Pre-maintenance", "warning"),
        (MAINTENANCE, "Maintenance", "warning"),
        (POST_MAINTENANCE, "Post-maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
        (DECOMMISSIONING, "Decommissioning", "warning"),
        (DECOMMISSIONED, "Decommissioned", "danger"),
    )


class BGPState(ChoiceSet):
    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPENSENT = "opensent"
    OPENCONFIRM = "openconfirm"
    ESTABLISHED = "established"

    CHOICES = (
        (IDLE, "Idle"),
        (CONNECT, "Connect"),
        (ACTIVE, "Active"),
        (OPENSENT, "OpenSent"),
        (OPENCONFIRM, "OpenConfirm"),
        (ESTABLISHED, "Established"),
    )


class IPFamily(ChoiceSet):
    ALL = 0
    IPV4 = 4
    IPV6 = 6

    CHOICES = ((ALL, "All"), (IPV4, "IPv4"), (IPV6, "IPv6"))


class RoutingPolicyType(ChoiceSet):
    EXPORT = "export-policy"
    IMPORT = "import-policy"
    IMPORT_EXPORT = "import-export-policy"

    CHOICES = ((EXPORT, "Export"), (IMPORT, "Import"), (IMPORT_EXPORT, "Import+Export"))


class PolicyTermAction(ChoiceSet):
    """Action taken by a routing-policy term (or the policy default-action)."""

    ACCEPT = "accept"
    REJECT = "reject"
    NEXT_TERM = "next-term"
    NEXT_POLICY = "next-policy"

    CHOICES = (
        (ACCEPT, "Accept", "success"),
        (REJECT, "Reject", "danger"),
        (NEXT_TERM, "Next term", "secondary"),
        (NEXT_POLICY, "Next policy", "secondary"),
    )
