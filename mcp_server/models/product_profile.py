"""
Product Profile Enum for role-based access control
"""
from enum import Enum


class ProductProfile(Enum):
    """Product profiles for RBAC"""

    COMMON = "common"
    ADMIN = "admin"
    PREMIUM = "premium"
    BASIC = "basic"

    @classmethod
    def from_code(cls, code: str) -> 'ProductProfile':
        """Get ProductProfile from code string"""
        code = code.lower()
        for profile in cls:
            if profile.value == code:
                return profile
        return cls.COMMON

    @property
    def code(self) -> str:
        """Get profile code"""
        return self.value

    def __str__(self) -> str:
        return self.value

