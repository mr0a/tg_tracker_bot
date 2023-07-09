from tortoise import fields
from tortoise.models import Model


class User(Model):
    chat_id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=255)

    def __str__(self):
        return f"User(chat_id={self.chat_id}, user_name='{self.user_name}')"


class Trackers(Model):
    user = fields.ForeignKeyField('models.User', related_name='trackers')
    token_name = fields.CharField(max_length=255)
    time_interval = fields.CharField(max_length=255)
    price_tick = fields.DecimalField(max_digits=10, decimal_places=2)
    executor = fields.CharField(max_length=64)

    def __str__(self):
        return f"Trackers(chat_id={self.user}, token_name='{self.token_name}', time_interval='{self.time_interval}', price_tick={self.price_tick})"


class ChannelTracker(Model):
    user = fields.ForeignKeyField('models.User', related_name='channelTracker')
    channel_id = fields.CharField(max_length=255)
    joined = fields.BooleanField(default=False)
    pattern = fields.CharField(max_length=255, null=True)
    cron_interval = fields.CharField(max_length=255)
    last_tracked_id = fields.BigIntField(null=True)

    def __str__(self) -> str:
        return f"ChannelTracker(user={self.user}, channel_id={self.channel_id}, joined={self.joined}, pattern={self.pattern}, time_interval={self.cron_interval})"
