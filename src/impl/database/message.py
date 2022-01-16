from typing import Optional

from ormar import BigInteger, ForeignKey, Model

from .channel import Channel
from .metadata import database, metadata
from .user import User


class MessageFlags:
    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def DELETED(self) -> bool:
        return bool(self.value & 1)


class Message(Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "messages"

    # pyright: reportGeneralTypeIssues=false
    id: int = BigInteger(primary_key=True)
    original_id: Optional[int] = BigInteger(nullable=True)
    flags: int = BigInteger(default=0)
    channel: Channel = ForeignKey(Channel)
    user: User = ForeignKey(User)
    channel_id: int = BigInteger()
    guild_id: int = BigInteger()
    webhook_id: Optional[int] = BigInteger(nullable=True)

    @property
    def message_flags(self) -> MessageFlags:
        return MessageFlags(self.flags)
