from rest_framework.exceptions import PermissionDenied

from .models import Notification


def notify(*, recipient, type: str, message: str, link: str = "") -> Notification:
    return Notification.objects.create(recipient=recipient, type=type, message=message, link=link)


def notify_many(*, recipients, type: str, message: str, link: str = "") -> None:
    Notification.objects.bulk_create(
        Notification(recipient=recipient, type=type, message=message, link=link)
        for recipient in recipients
    )


def mark_read(*, notification: Notification, acting_user) -> Notification:
    if notification.recipient_id != acting_user.id:
        raise PermissionDenied("You can only mark your own notifications as read.")
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
    return notification


def mark_all_read(*, acting_user) -> None:
    Notification.objects.filter(recipient=acting_user, is_read=False).update(is_read=True)
