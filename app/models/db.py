from tortoise import fields
from tortoise.models import Model


class Session(Model):
    id = fields.CharField(pk=True, max_length=100)
    title = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sessions"


class Message(Model):
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField("models.Session", related_name="messages", on_delete=fields.CASCADE)
    role = fields.CharField(max_length=20)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"
        ordering = ["created_at"]