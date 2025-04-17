from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ---------------- Public Views ----------------
    path('', views.menu_view, name='menu'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/',
         views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('vendor/<int:vendor_id>/',
         views.vendor_food_items_view, name='vendor_food_items'),
    path('search/', views.search_results, name='search_results'),

    # ---------------- User Profile & Wallet ----------------
    path('profile/', views.profile, name='profile'),

    # ---------------- Auth Views ----------------
    path('login/', views.login_view, name='login'),
    # Update signup path to step1
    path('signup/', views.signup_step1, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('signup/success/', views.signup_success, name='signup_success'),


    # ---------------- Admin Views ----------------
    path('admin/manage-food-items/',
         views.manage_food_items, name='manage_food_items'),
    path('admin/edit-food-item/<int:item_id>/',
         views.edit_food_item, name='edit_food_item'),
    path('admin/delete-food-item/<int:item_id>/',
         views.delete_food_item, name='delete_food_item'),
    path('admin/manage-orders/', views.manage_orders, name='manage_orders'),
    path('admin/update-order-status/<int:order_id>/',
         views.update_order_status, name='update_order_status'),


    path('reset_password/', auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('reset_password_done/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
