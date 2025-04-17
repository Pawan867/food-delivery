from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Vendor, Category, FoodItem, Order, OrderItem, UserProfile, CartItem, Transaction, Subscription

# Vendor model registration


class VendorAdmin(ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'phone')
    list_filter = ('name',)


admin.site.register(Vendor, VendorAdmin)

# Category model registration


class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'vendor')
    search_fields = ('name', 'vendor__name')
    list_filter = ('vendor',)


admin.site.register(Category, CategoryAdmin)

# FoodItem model registration


class FoodItemAdmin(ModelAdmin):
    list_display = ('name', 'vendor', 'general_category',
                    'vendor_category', 'price', 'available', 'rating')
    search_fields = ('name', 'general_category__name', 'vendor__name')
    list_filter = ('general_category', 'vendor_category',
                   'available', 'rating')
    list_editable = ('price', 'available')


admin.site.register(FoodItem, FoodItemAdmin)

# Order model registration


class OrderAdmin(ModelAdmin):
    list_display = ('id', 'name', 'phone', 'total', 'created_at')
    search_fields = ('name', 'phone', 'address')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'


admin.site.register(Order, OrderAdmin)

# OrderItem model registration


class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'subtotal')
    search_fields = ('order__id', 'item__name')
    list_filter = ('order',)


admin.site.register(OrderItem, OrderItemAdmin)

# UserProfile model registration


class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone', 'address', 'profile_image')
    search_fields = ('user__username', 'phone')
    list_filter = ('user',)


admin.site.register(UserProfile, UserProfileAdmin)

# CartItem model registration


class CartItemAdmin(ModelAdmin):
    list_display = ('user', 'food_item', 'quantity', 'status', 'added_at')
    search_fields = ('user__username', 'food_item__name')
    list_filter = ('status', 'user')


admin.site.register(CartItem, CartItemAdmin)

# Transaction model registration


class TransactionAdmin(ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type',
                    'payment_method', 'timestamp')
    search_fields = ('user__username', 'transaction_type', 'payment_method')
    list_filter = ('transaction_type', 'payment_method', 'timestamp')
    date_hierarchy = 'timestamp'


admin.site.register(Transaction, TransactionAdmin)

# Subscription model registration


class SubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'plan_name', 'price',
                    'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'plan_name')
    list_filter = ('is_active', 'start_date', 'end_date')
    date_hierarchy = 'start_date'


admin.site.register(Subscription, SubscriptionAdmin)
