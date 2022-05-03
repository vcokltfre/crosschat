from __future__ import annotations

from traceback import format_exc
from typing import TYPE_CHECKING

from disnake import AllowedMentions, Embed
from disnake import Message as DiscordMessage
from disnake import TextChannel, Webhook
from disnake.http import Route
from loguru import logger

from src.impl.database import Channel, ChannelMap, Message, User

if TYPE_CHECKING:
    from src.impl.bot import Bot

WEBHOOK_THRESHOLD = 1


def filter_content(text: str) -> str:
    return text.replace(")[", ")​[")


class ChannelManager:
    def __init__(self, bot: Bot, channel: Channel) -> None:
        self.bot = bot
        self.channel = channel

        self.channels: dict[int, list[Webhook]] = dict()

    def handles(self, channel_id: int) -> bool:
        return channel_id in self.channels

    async def _resolve_webhooks(self, channel_id: int, required: int = 1) -> list[Webhook]:
        current = self.channels.get(channel_id, [])

        if len(current) >= required:
            return current

        channel = self.bot.get_channel(channel_id)
        assert isinstance(channel, TextChannel)

        current = [
            webhook for webhook in await channel.webhooks() if webhook.user and webhook.user.id == self.bot.user.id
        ]

        needed = required - len(current)

        for i in range(needed):
            current.append(await channel.create_webhook(name="CrossChat"))

        self.channels[channel_id] = current

        return current

    async def _send_to_channel(
        self,
        channel_id: int,
        username: str,
        avatar: str,
        content: str,
        embeds: list[Embed] = None,
        allowed_mentions: AllowedMentions = AllowedMentions(
            everyone=False,
            roles=False,
            users=False,
        ),
    ) -> DiscordMessage:
        webhooks = await self._resolve_webhooks(channel_id, WEBHOOK_THRESHOLD)

        embeds = embeds or []

        return await webhooks[0].send(
            filter_content(content), username=username, avatar_url=avatar, embeds=embeds, allowed_mentions=allowed_mentions, wait=True
        )

    async def _edit_message(
        self,
        message_id: int,
        channel_id: int,
        webhook_id: int,
        content: str,
        embeds: list[Embed] = None,
    ) -> None:
        webhooks = await self._resolve_webhooks(channel_id, WEBHOOK_THRESHOLD)

        found = None

        for webhook in webhooks:
            if webhook.id == webhook_id:
                found = webhook
                break

        if not found:
            logger.warning(
                f"Failed to find webhook {webhook_id} for message {message_id} on virtual channel {channel_id}"
            )
            return

        embeds = embeds or []

        await found.edit_message(message_id, content=filter_content(content), embeds=embeds)

    async def _delete_message(self, message_id: int, channel_id: int, webhook_id: int) -> None:
        webhooks = await self._resolve_webhooks(channel_id, WEBHOOK_THRESHOLD)

        found = None

        for webhook in webhooks:
            if webhook.id == webhook_id:
                found = webhook
                break

        if not found:
            return

        await found.delete_message(message_id)

    async def setup(self) -> None:
        mappings = await ChannelMap.objects.filter(channel=self.channel.name).all()

        self.channels = {mapping.channel_id: [] for mapping in mappings}

    async def join(self, channel_id: int, thread_id: int = None) -> None:
        await ChannelMap(channel=self.channel.name, channel_id=channel_id, thread_id=thread_id).save()

        self.channels[channel_id] = []

    async def leave(self, channel_id: int) -> None:
        await ChannelMap.objects.filter(channel=self.channel.name, channel_id=channel_id).delete()

        self.channels.pop(channel_id, None)

    async def send(
        self,
        username: str,
        avatar: str,
        content: str,
        origin: DiscordMessage = None,
        user: User = None,
        embeds: list[Embed] = None,
        allowed_mentions: AllowedMentions = AllowedMentions(
            everyone=False,
            roles=False,
            users=False,
        ),
    ) -> None:
        sent: dict[int, DiscordMessage] = {}
        failed = 0

        fid = f"{origin.channel.id}:{origin.id}" if origin else None

        logger.info(f"Sending message {fid} to virtual channel {self.channel.name}")

        for channel in self.channels:
            if origin and channel == origin.channel.id:
                continue

            try:
                sent[channel] = await self._send_to_channel(
                    channel,
                    username,
                    avatar,
                    content,
                    embeds,
                    allowed_mentions,
                )

                logger.info(f"Sent message {fid} to virtual channel {channel}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send message {fid} to virtual channel {channel}:\n{format_exc()}")

        logger.info(f"Sent message {fid} to {len(sent) - failed} virtual channels. (failed: {failed})")

        if not (origin and user):
            return

        assert origin.guild

        await Message(
            id=origin.id,
            channel=self.channel.name,
            user=user.id,
            channel_id=origin.channel.id,
            guild_id=origin.guild.id,
            original_id=origin.id,
        ).save()

        await Message.objects.bulk_create(
            [
                Message(
                    id=v.id,
                    channel=self.channel.name,
                    user=user.id,
                    channel_id=v.channel.id,
                    guild_id=v.guild.id,
                    original_id=origin.id,
                    webhook_id=v.author.id,
                )
                for v in sent.values()
                if v.guild
            ]
        )

    async def edit(
        self,
        id: int,
        content: str,
        embeds: list[Embed] = None,
    ) -> None:
        messages = await Message.objects.filter(channel=self.channel.name, original_id=id).all()

        logger.info(f"Editing {len(messages)} messages on virtual channel {self.channel.name} for message {id}")

        for message in messages:
            if not message.webhook_id:
                continue

            try:
                await self._edit_message(message.id, message.channel_id, message.webhook_id, content, embeds)
            except Exception as e:
                logger.error(
                    f"Failed to edit message {message.id} on virtual channel {message.channel_id}:\n{format_exc()}"
                )

    async def delete(self, id: int) -> None:
        message = await Message.objects.filter(channel=self.channel.name, id=id).first()

        messages = await Message.objects.filter(channel=self.channel.name, original_id=message.original_id).all()

        logger.info(f"Deleting {len(messages)} messages on virtual channel {self.channel.name} for message {id}")

        for message in messages:
            if not message.webhook_id:
                try:
                    route = Route(
                        "DELETE",
                        "/channels/{channel_id}/messages/{message_id}",
                        channel_id=message.channel_id,
                        message_id=message.id,
                    )
                    await self.bot.http.request(route)
                except Exception as e:
                    logger.error(
                        f"Failed to delete message {message.id} on virtual channel {message.channel_id}:\n{format_exc()}"
                    )
                finally:
                    continue

            try:
                await self._delete_message(message.id, message.channel_id, message.webhook_id)
            except Exception as e:
                logger.error(
                    f"Failed to delete message {message.id} on virtual channel {message.channel_id}:\n{format_exc()}"
                )
