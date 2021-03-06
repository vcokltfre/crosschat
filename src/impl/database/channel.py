from typing import Optional

from ormar import BigInteger, ForeignKey, Model, String

from .metadata import database, metadata


class ChannelFlags:
    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def PUBLIC(self) -> bool:
        return bool(self.value & 1)


class Channel(Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "channels"

    # pyright: reportGeneralTypeIssues=false
    name: str = String(max_length=255, primary_key=True)
    flags: int = BigInteger(default=0)

    @property
    def channel_flags(self) -> ChannelFlags:
        return ChannelFlags(self.flags)


class ChannelMap(Model):
    class Meta:
        database = database
        metadata = metadata
        tablename = "channel_map"

    # pyright: reportGeneralTypeIssues=false
    channel_id: int = BigInteger(primary_key=True)
    thread_id: Optional[int] = BigInteger(nullable=True)
    channel: Channel = ForeignKey(Channel)
