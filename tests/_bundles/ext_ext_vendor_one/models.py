from ..vendor_one.models import (
    OneUser as BaseOneUser,
    OneRole as BaseOneRole,
)


class OneUser(BaseOneUser):
    class Meta:
        lazy_mapping = True


class OneRole(BaseOneRole):
    pass
