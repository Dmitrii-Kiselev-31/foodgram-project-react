from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole:
    USER = 'user'
    ADMIN = 'admin'
    choices = [
        (USER, 'USER'),
        (ADMIN, 'ADMIN')
    ]


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Username')
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Email')
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='First name')
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Last name')
    role = models.TextField(
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name='User role')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_user(self):
        return self.role == UserRole.USER

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['username']

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Subscriber',
        db_index=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Recipe author',
        db_index=False)

    class Meta:
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author')]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
