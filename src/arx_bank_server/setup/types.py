# create enum for auth status
from enum import Enum


class DetectionStatus(str, Enum):
    OK = "ok"
    NO_USER = "no_user"
    TOO_MANY_USERS = "too_many_users"
    UNKNOWN_USER = "unknown"
    WRONG_USER = "wrong_user"
