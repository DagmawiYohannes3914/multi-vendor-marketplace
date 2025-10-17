from .models import Notification


def create_notification(user, notification_type, title, message, reference_id=""):
    """
    Create a notification for a user
    
    Args:
        user: User object
        notification_type: Type of notification (from Notification.NOTIFICATION_TYPES)
        title: Notification title
        message: Notification message
        reference_id: Optional reference ID (e.g., order ID)
    
    Returns:
        Notification object
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        reference_id=reference_id
    )