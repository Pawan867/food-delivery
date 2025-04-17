from restaurant.models import Category, FoodItem, Vendor
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, FoodItem, Order, OrderItem, Vendor, UserProfile, CartItem, Transaction, Subscription
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth import login, logout
from .forms import LoginForm  # LoginForm import गर्न
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from datetime import datetime, timedelta
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)

from social_django.utils import psa

# ---------------- Public Views ----------------


def menu_view(request):
    categories = Category.objects.all()
    foods = FoodItem.objects.filter(available=True)

    # Paginate vendors
    vendors_list = Vendor.objects.all()
    paginator = Paginator(vendors_list, 9)  # Show 9 vendors per page
    page_number = request.GET.get('page')
    vendors = paginator.get_page(page_number)

    return render(request, 'restaurant/menu.html', {
        'categories': categories,
        'foods': foods,
        'vendors': vendors,
    })


@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for item_id_str, quantity in cart.items():
        try:
            item = get_object_or_404(FoodItem, pk=int(item_id_str))
            subtotal = item.price * quantity
            cart_items.append(
                {'item': item, 'quantity': quantity, 'subtotal': subtotal})
            total += subtotal
        except (ValueError, FoodItem.DoesNotExist):
            continue
    return render(request, 'restaurant/cart.html', {'cart_items': cart_items, 'total': total})


@login_required(login_url='/login/')
def add_to_cart(request, item_id):
    cart = request.session.get('cart', {})
    total_items = request.session.get('total_items', 0)
    item_id_str = str(item_id)

    cart[item_id_str] = cart.get(item_id_str, 0) + 1
    total_items += 1

    request.session['cart'] = cart
    request.session['total_items'] = total_items
    request.session.modified = True

    # Use 'next' parameter if available, otherwise fallback to 'menu'
    next_url = request.POST.get('next') or request.GET.get('next') or 'menu'
    return redirect(next_url)


@login_required
def remove_from_cart(request, item_id):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    if item_id_str in cart:
        del cart[item_id_str]
    request.session['cart'] = cart
    request.session['total_items'] = sum(cart.values())
    request.session.modified = True
    return redirect('cart')


@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for item_id_str, quantity in cart.items():
        try:
            item = FoodItem.objects.get(pk=int(item_id_str))
            subtotal = item.price * quantity
            cart_items.append(
                {'item': item, 'quantity': quantity, 'subtotal': subtotal})
            total += subtotal
        except (ValueError, FoodItem.DoesNotExist):
            continue
    return render(request, 'restaurant/checkout.html', {'cart_items': cart_items, 'total': total})


@login_required
def place_order(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, 'Your cart is empty.')
            return redirect('menu')

        order_total = 0
        order_items = []
        for item_id_str, quantity in cart.items():
            try:
                item = FoodItem.objects.get(pk=int(item_id_str))
                subtotal = item.price * quantity
                order_total += subtotal
                order_items.append(
                    {'item': item, 'quantity': quantity, 'subtotal': subtotal})
            except (ValueError, FoodItem.DoesNotExist):
                continue

        order = Order.objects.create(
            name=name,
            phone=phone,
            address=address,
            total=order_total,
            user=request.user if request.user.is_authenticated else None
        )

        for order_item in order_items:
            OrderItem.objects.create(
                order=order,
                item=order_item['item'],
                quantity=order_item['quantity'],
                subtotal=order_item['subtotal']
            )

        if request.user.is_authenticated:
            # No need to get UserProfile or user_profile
            Transaction.objects.create(
                user=request.user,  # Use the user directly
                amount=-order_total,
                description='Order Payment',
                payment_method='WALLET'  # Update with the correct payment method if needed
            )

        request.session.pop('cart', None)
        request.session['total_items'] = 0
        request.session.modified = True
        messages.success(request, f'Order placed! Total: Rs. {order_total}')
        return redirect('menu')
    return HttpResponse(status=405)


def vendor_food_items_view(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    foods_list = FoodItem.objects.filter(vendor=vendor, available=True)
    paginator = Paginator(foods_list, 9)  # Show 9 items per page
    page_number = request.GET.get('page')
    foods = paginator.get_page(page_number)
    return render(request, 'restaurant/vendor_food_items.html', {
        'vendor': vendor,
        'foods': foods
    })


def search_results(request):
    query = request.GET.get('query', '')
    results = FoodItem.objects.filter(name__icontains=query)
    return render(request, 'search_results.html', {'results': results, 'query': query})


def login_view(request):
    return render(request, 'restaurant/login.html')

# ---------------- User Profile & Wallet ----------------


@login_required
def profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        profile_form = UserProfileForm(instance=profile)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    cancelled_orders = orders.filter(status='cancelled')
    transactions = Transaction.objects.filter(
        user=request.user).order_by('-timestamp')

    context = {
        'profile_form': profile_form,
        'orders': orders,
        'cancelled_orders': cancelled_orders,
        'transactions': transactions,
    }

    return render(request, 'restaurant/user_profile.html', context)


# ---------------- Admin Views ----------------


@staff_member_required
def manage_food_items(request):
    food_items = FoodItem.objects.all()
    return render(request, 'restaurant/manage_food_items.html', {'food_items': food_items})


@staff_member_required
def edit_food_item(request, item_id):
    item = get_object_or_404(FoodItem, pk=item_id)
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.price = request.POST.get('price')
        item.description = request.POST.get('description')
        item.available = request.POST.get('available') == 'on'
        item.save()
        messages.success(request, 'Food item updated successfully!')
        return redirect('manage_food_items')
    return render(request, 'restaurant/edit_food_item.html', {'item': item})


@staff_member_required
def delete_food_item(request, item_id):
    item = get_object_or_404(FoodItem, pk=item_id)
    item.delete()
    messages.success(request, 'Food item deleted successfully!')
    return redirect('manage_food_items')


@staff_member_required
def manage_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'restaurant/manage_orders.html', {'orders': orders})


@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
        messages.success(
            request, f'Order {order.id} status updated to {order.status}.')
        return redirect('manage_orders')
    return render(request, 'restaurant/update_order_status.html', {'order': order})


# ---------------- Logout ----------------


def login_view(request):
    next_url = request.GET.get('next', '/')
    if request.method == 'POST':
        form = LoginForm(data=request.POST)  # Use custom form
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'restaurant/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('menu')


def signup_step1(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        # Phone validation
        if not phone or len(phone) != 10 or not phone.isdigit():
            messages.error(
                request, "Please enter a valid 10-digit phone number.")
            return render(request, 'restaurant/signup_step1.html')

        if User.objects.filter(username=phone).exists():
            messages.error(request, "This phone number is already registered.")
            return render(request, 'restaurant/signup_step1.html')

        # Email validation
        if not email:
            messages.error(request, "Email is required.")
            return render(request, 'restaurant/signup_step1.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'restaurant/signup_step1.html')

        # Generate and store OTP
        otp = str(random.randint(100000, 999999))
        otp_created_at = timezone.now()

        # Store in session
        request.session['temp_phone'] = phone
        request.session['temp_email'] = email
        request.session['otp'] = otp
        request.session['otp_created_at'] = otp_created_at.strftime(
            '%Y-%m-%d %H:%M:%S')

        # Send OTP to email
        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP code is: {otp}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent to your email.")
        return redirect('verify_otp')

    return render(request, 'restaurant/signup_step1.html')


def verify_otp(request):
    phone = request.session.get('temp_phone')
    email = request.session.get('temp_email')
    session_otp = request.session.get('otp')
    otp_created_at_str = request.session.get('otp_created_at')

    # Session validation
    if not phone or not email or not session_otp or not otp_created_at_str:
        messages.error(request, "Session expired or invalid access.")
        return redirect('signup_step1')

    # OTP Expiry check
    otp_created_at = timezone.make_aware(
        datetime.strptime(otp_created_at_str, '%Y-%m-%d %H:%M:%S'))
    if timezone.now() > otp_created_at + timedelta(minutes=5):
        messages.error(request, "OTP expired. Please request a new OTP.")
        return redirect('resend_otp')

    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        user_form = SignUpForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        # OTP match check
        if user_otp != session_otp:
            messages.error(request, "Incorrect OTP.")
        else:
            # Form validation
            if user_form.is_valid() and profile_form.is_valid():
                # Save user details and set email
                user = user_form.save(commit=False)
                user.username = phone
                user.email = email  # Store email here
                user.save()

                # Save the user profile and set phone and email
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.phone = phone
                profile.email = email  # Store email in UserProfile
                profile.save()

                # Clear session variables
                for key in ['temp_phone', 'temp_email', 'otp', 'otp_created_at']:
                    request.session.pop(key, None)

                # Auto-login user after signup
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name}!")
                return redirect('profile')
            else:
                messages.error(request, "Please correct the form errors.")
    else:
        user_form = SignUpForm()
        profile_form = UserProfileForm()

    return render(request, 'restaurant/verify_otp.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'phone': phone,
        'email': email
    })


def resend_otp(request):
    phone = request.session.get('temp_phone')
    email = request.session.get('temp_email')

    if not phone or not email:
        messages.error(request, "Session expired. Please start again.")
        return redirect('signup_step1')

    # Prevent frequent OTP resends (wait at least 5 mins)
    otp_created_at_str = request.session.get('otp_created_at')
    if otp_created_at_str:
        otp_created_at = timezone.make_aware(
            datetime.strptime(otp_created_at_str, '%Y-%m-%d %H:%M:%S'))
        if timezone.now() < otp_created_at + timedelta(minutes=5):
            messages.info(
                request, "You can request a new OTP after 5 minutes.")
            return redirect('verify_otp')

    # Generate and store new OTP
    otp = str(random.randint(100000, 999999))
    otp_created_at = timezone.now()

    request.session['otp'] = otp
    request.session['otp_created_at'] = otp_created_at.strftime(
        '%Y-%m-%d %H:%M:%S')

    # Send new OTP
    send_mail(
        subject='Your New OTP Code',
        message=f'Your new OTP code is: {otp}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    messages.success(request, "New OTP sent to your email.")
    return redirect('verify_otp')


def signup_success(request):
    return render(request, 'restaurant/signup_success.html')


def password_reset(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        try:
            user_profile = UserProfile.objects.get(phone=phone)
            email = user_profile.email  # Fetch the email from UserProfile

            if email:
                # Generate OTP and send it to the email
                otp = str(random.randint(100000, 999999))
                send_mail(
                    subject='Password Reset OTP',
                    message=f'Your OTP is: {otp}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                request.session['reset_otp'] = otp
                request.session['user_profile_id'] = user_profile.id

                messages.success(request, "OTP sent to your email.")
                return redirect('reset_otp_verification')
            else:
                messages.error(
                    request, "Email not found for this phone number.")
        except UserProfile.DoesNotExist:
            messages.error(request, "No account found with this phone number.")
    return render(request, 'restaurant/password_reset.html')
# Social Auth Login view
@psa('social:complete')
def social_login(request, backend):
    # This view will be triggered when a user logs in using Google or Facebook.
    user = request.user
    if user.is_authenticated:
        login(request, user)
        return redirect('profile')  # Redirect to profile or another page after login.
    return redirect('login')

# You can also manually trigger actions after the login:
def social_auth_callback(request, backend):
    user = request.user
    if user.is_authenticated:
        # Perform actions like updating user profile here
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            # Populate user profile data if new
            profile.save()
        messages.success(request, 'Logged in successfully via ' + backend)
        return redirect('profile')
    return redirect('login')

# Optional: Logout view
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('menu')