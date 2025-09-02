import enum


class ReplicaReadStrategy(enum.StrEnum):
    DISTRIBUTED = enum.auto()
    SEQUENTIAL = enum.auto()
