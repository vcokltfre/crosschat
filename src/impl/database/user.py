from ormar import BigInteger, Boolean, Model, String

from .metadata import database, metadata


class UserFlags:
    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def DEVELOPER(self) -> bool:
        return bool(self.value & 1)

    @property
    def MODERATOR(self) -> bool:
        return bool(self.value & 2)

    @property
    def ADMIN(self) -> bool:
        return bool(self.value & 4)


class User(Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "users"

    # pyright: reportGeneralTypeIssues=false
    id: int = BigInteger(primary_key=True)
    name: str = String(max_length=255)
    flags: int = BigInteger(default=0)
    banned: bool = Boolean(default=False)

    @property
    def user_flags(self) -> UserFlags:
        return UserFlags(self.flags)

    @property
    def badges(self) -> str:
        if self.user_flags.DEVELOPER:
            return " ⚙️"
        if self.user_flags.ADMIN:
            return " ⚒️"
        if self.user_flags.MODERATOR:
            return " 🔨"

        return ""
