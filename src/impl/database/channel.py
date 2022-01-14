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
    id: int = BigInteger(primary_key=True)
    name: str = String(max_length=255)
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
    channel: Channel = ForeignKey(Channel)
