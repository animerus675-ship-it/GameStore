from django.conf import settings
from django.db import models

from catalog.models import Game


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.user})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("order", "game")

    def __str__(self):
        return f"{self.game} x {self.quantity}"


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for order #{self.order_id}"
