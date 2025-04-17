from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# Vendor Model


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    address = models.TextField()
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(max_length=15, validators=[phone_validator])
    logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Category Model
class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('VENDOR', 'Vendor-specific'),
        ('GENERAL', 'General (Shared across vendors)'),
    ]

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='categories', blank=True, null=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    category_type = models.CharField(
        max_length=10, choices=CATEGORY_TYPE_CHOICES, default='GENERAL')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.vendor.name if self.vendor else 'General'}"


# FoodItem Model
class FoodItem(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='food_items')
    general_category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='general_food_items', blank=True, null=True)
    vendor_category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='vendor_food_items', blank=True, null=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='food_images/')
    available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Validation to ensure at least one category is selected
        if not self.general_category and not self.vendor_category:
            raise ValidationError(
                'At least one category (General or Vendor-specific) must be selected for the food item.')

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"


# Review Model (Rating and Comments for FoodItem)
class Review(models.Model):
    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(
        1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.food_item.name} by {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the food item's average rating after review is added
        self.food_item.update_average_rating()


# Function to update the average rating of FoodItem
def update_average_rating(self):
    reviews = self.reviews.all()
    total_rating = sum([review.rating for review in reviews])
    total_reviews = reviews.count()
    if total_reviews > 0:
        self.rating = total_rating / total_reviews
    else:
        self.rating = 0
    self.save()


FoodItem.update_average_rating = update_average_rating


# Order Model
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=ORDER_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


# OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


# User Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(
        upload_to='user_profiles/', blank=True, null=True)
    phone_validator = RegexValidator(
        regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")
    phone = models.CharField(max_length=15, blank=True,
                             null=True, validators=[phone_validator])
    address = models.TextField(blank=True, null=True)

    # New fields to store social login details
    google_id = models.CharField(max_length=255, blank=True, null=True)
    facebook_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# CartItem Model
class CartItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='cart_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=[(
        'IN_CART', 'In Cart'), ('REMOVED', 'Removed')], default='IN_CART')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_item.name} x {self.quantity}"

    def get_total_price(self):
        return self.food_item.price * self.quantity


# Transaction Model
class Transaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('CASH_ON_DELIVERY', 'Cash on Delivery'),
        ('WALLET', 'Wallet'),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=[('CREDIT', 'Credit'), ('DEBIT', 'Debit')])
    description = models.TextField()
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - Rs. {self.amount} ({self.payment_method})"


# Subscription Model
class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"


# Coupon Model (new)
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    expiration_date = models.DateTimeField()

    def __str__(self):
        return f"Coupon: {self.code} - {self.discount_percentage}% off"
