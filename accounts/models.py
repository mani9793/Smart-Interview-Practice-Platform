from django.db import models
from django.conf import settings


class AppUser(models.Model):
    """
    App-level user record. Stored in table 'users' (not auth_user).
    One-to-one with Django's auth User for login; this table holds our app user data.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='app_user',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.user.username
