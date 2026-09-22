from enum import StrEnum


class TableStatus(StrEnum):
    PROPOSING = "proposing"
    VOTING = "voting"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ParticipantRole(StrEnum):
    HOST = "host"
    GUEST = "guest"


class MembershipStatus(StrEnum):
    INVITED = "invited"
    CONFIRMED = "confirmed"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    SKIPPED = "skipped"
