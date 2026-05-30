from utils.enums import ChoiceSet


class CommunityKind(ChoiceSet):
    STANDARD = "standard"
    EXTENDED = "extended"
    LARGE = "large"

    CHOICES = (
        (STANDARD, "Community"),
        (EXTENDED, "Extended Community"),
        (LARGE, "Large Community"),
    )


class CommunityType(ChoiceSet):
    EGRESS = "egress"
    INGRESS = "ingress"

    CHOICES = ((EGRESS, "Egress"), (INGRESS, "Ingress"))


class PrefixListFamily(ChoiceSet):
    ANY = 0
    IPV4 = 4
    IPV6 = 6

    CHOICES = ((ANY, "Any"), (IPV4, "IPv4"), (IPV6, "IPv6"))


class PrefixListMatchType(ChoiceSet):
    """
    Per-member prefix match qualifiers, mirroring Nokia SR OS prefix-list
    match types. Stored on each prefix-list member so the policy preview can
    render the appropriate qualifier.
    """

    EXACT = "exact"
    LONGER = "longer"
    ORLONGER = "orlonger"
    THROUGH = "through"
    UPTO = "upto"
    PREFIX_LENGTH_RANGE = "prefix-length-range"
    ADDRESS_MASK = "address-mask"

    CHOICES = (
        (EXACT, "exact"),
        (LONGER, "longer"),
        (ORLONGER, "orlonger"),
        (THROUGH, "through"),
        (UPTO, "upto"),
        (PREFIX_LENGTH_RANGE, "prefix-length-range"),
        (ADDRESS_MASK, "address-mask"),
    )
