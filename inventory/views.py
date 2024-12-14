from django.utils import timezone

from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from pyexpat.errors import messages
from django.contrib import messages

from . import models
from .models import Uniform, Order, Payment, UserProfile, Uniform, SearchLog, EditLog, Order, CartItem, Cart
from .forms import UniformForm, OrderForm, UserProfileForm, LoginForm, SignupForm, UniformForm, ProfileForm
import requests
import csv
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count


def redirect_home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:  # Admin user check
            return redirect('admin_home')  # Redirect to the admin dashboard
        else:
            return redirect('customer_page')  # Redirect to the customer page
    return redirect('login')


def home(request):
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='COMPLETED').count()
    total_revenue = Order.objects.filter(status='COMPLETED').aggregate(total=Sum('total_price'))['total'] or 0
    recent_orders = Order.objects.order_by('-order_date')[:5]

    return render(request, 'home.html', {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    })

def add_uniform(request):
    if request.method == 'POST':
        form = UniformForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Uniform added successfully.")
            return redirect('manage_uniforms')  # Ensure this matches the name in urls.py
        else:
            messages.error(request, "There was an error adding the uniform.")
    else:
        form = UniformForm()

    return render(request, 'add_uniform.html', {'form': form})

def place_order(request, uniform_id):
    uniform = get_object_or_404(Uniform, id=uniform_id)

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.uniform = uniform
            order.save()
            return redirect('initiate_payment', order_id=order.id)
    else:
        form = OrderForm()

    return render(request, 'place_order.html', {'uniform': uniform, 'form': form})
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    mpesa_endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    access_token = get_mpesa_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": settings.MPESA_PASSWORD,
        "Timestamp": settings.MPESA_TIMESTAMP,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(order.total_price),
        "PartyA": request.user.userprofile.phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": request.user.userprofile.phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"Order-{order.id}",
        "TransactionDesc": "Payment for Uniform Order"
    }
    response = requests.post(mpesa_endpoint, json=payload, headers=headers)
    if response.status_code == 200:
        return JsonResponse({"message": "Payment initiated successfully."})
    return JsonResponse({"error": "Failed to initiate payment."}, status=400)

def get_mpesa_access_token():
    token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(token_url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json().get("access_token")

def download_inventory_report(request):
    uniforms = Uniform.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Size', 'Quantity', 'Price', 'Supplier', 'Date Added'])
    for uniform in uniforms:
        writer.writerow([uniform.name, uniform.category, uniform.size, uniform.quantity, uniform.price, uniform.supplier, uniform.date_added])

    return response


def search_uniform(request):
    query = request.GET.get('query', '')  # Get the search query from the request
    uniforms = Uniform.objects.all()  # Default to all uniforms

    if query:
        # Filter uniforms by name (case-insensitive)
        uniforms = uniforms.filter(name__icontains=query)

    return render(request, 'search_results.html', {'uniforms': uniforms, 'query': query})
def customer_page(request):
    user_profile = UserProfile.objects.get(user=request.user)
    orders = Order.objects.filter(user=request.user)

    return render(request, 'customer_page.html', {
        'user_profile': user_profile,
        'orders': orders
    })
def sales_analytics(request):
    total_sales = Order.objects.aggregate(total_sales=Sum('total_price'))['total_sales']
    top_selling = Uniform.objects.annotate(total_quantity=Sum('order__quantity')).order_by('-total_quantity')[:5]

    return render(request, 'analytics.html', {
        'total_sales': total_sales,
        'top_selling': top_selling
    })
def low_stock_alert(request):
    uniforms = Uniform.objects.filter(quantity__lt=5)  # Example threshold for low stock
    return render(request, 'inventory_alert.html', {'uniforms': uniforms})

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to the correct page based on whether the user is an admin or not
                    if user.is_staff:
                        return redirect('admin_home')  # Redirect to admin dashboard
                    else:
                        return redirect('customer_page')  # Redirect to customer page
                else:
                    messages.error(request, 'Your account is inactive.')
                    return render(request, 'login.html', {'form': form})
            else:
                messages.error(request, 'Invalid username or password.')
                return render(request, 'login.html', {'form': form})
        else:
            # When form is invalid, render the form with errors
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        print("Received POST data:", request.POST)  # Log the POST data
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile(user=user, phone_number=form.cleaned_data['phone_number'])
            user_profile.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def manage_users(request):
    users = User.objects.all()  # Fetch all users
    return render(request, 'manage_users.html', {'users': users})
def admin_dashboard(request):
    # Fetch customer activity logs (example: search and edit logs)
    search_logs = SearchLog.objects.all().order_by('-timestamp')
    edit_logs = EditLog.objects.all().order_by('-timestamp')
    return render(request, 'home.html', {
        'search_logs': search_logs,
        'edit_logs': edit_logs
    })
def analytics(request):
    # Analytics data: total users, popular items, etc.
    total_users = User.objects.count()
    total_uniforms = Uniform.objects.count()
    popular_items = Uniform.objects.annotate(edit_count=Count('editlog')).order_by('-edit_count')[:5]
    return render(request, 'analytics.html', {
        'total_users': total_users,
        'total_uniforms': total_uniforms,
        'popular_items': popular_items
    })

def edit_uniform(request, uniform_id):
    # Fetch the uniform by its ID
    uniform = get_object_or_404(Uniform, id=uniform_id)

    if request.method == 'POST':
        # Populate the form with submitted data
        form = UniformForm(request.POST, instance=uniform)
        if form.is_valid():
            form.save()  # Save changes to the database
            return redirect('admin_home')  # Redirect to admin dashboard
    else:
        # Populate the form with the uniform's current data
        form = UniformForm(instance=uniform)

    return render(request, 'edit_uniform.html', {'form': form})
def manage_orders(request):
    orders = Order.objects.all().order_by('-order_date')  # Fetch all orders, most recent first
    return render(request, 'manage_orders.html', {'orders': orders})

def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_history.html', {'orders': orders})
def add_to_cart(request, uniform_id):
    uniform = Uniform.objects.get(id=uniform_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Check if the item is already in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, uniform=uniform)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = CartItem.objects.get(id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.uniform.price for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def checkout(request):
    if request.method == 'POST':
        # Get the cart items for the current user
        cart_items = Cart.objects.filter(user=request.user)

        # Get the shipping address and payment method from the form
        shipping_address = request.POST['address']
        payment_method = request.POST['payment_method']

        # Calculate the total price
        total_price = sum(item.price * item.quantity for item in cart_items)

        # Create the order object
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            total_price=total_price,
            payment_method=payment_method,
            status='PENDING',  # You can set initial status as PENDING
            order_date=timezone.now(),
        )

        # Optionally, save the cart items as order items (if needed)
        for item in cart_items:
            order.order_items.create(
                uniform=item.uniform,  # Assuming Cart model has a foreign key to Uniform
                quantity=item.quantity,
                price=item.price,
            )

        # Clear the user's cart after the order has been created
        cart_items.delete()

        # Redirect to a confirmation page or back to the home page
        return redirect('order_confirmation', order_id=order.id)

    else:
        # If it's a GET request, render the checkout page with the user's cart items
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(item.price * item.quantity for item in cart_items)

        context = {
            'cart_items': cart_items,
            'total_price': total_price,
        }
        return render(request, 'checkout.html', context)

# inventory/views.py
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order_confirmation.html', {'order': order})

from django.shortcuts import render

def customer_page(request):
    # Logic for customer page (show user orders, cart, etc.)
    return render(request, 'customer_page.html')


def manage_uniforms(request):
    # Fetch all uniforms from the database
    uniforms = Uniform.objects.all()

    # Render the manage_uniforms template with the uniforms data
    return render(request, 'manage_uniforms.html', {'uniforms': uniforms})
def delete_uniform(request, uniform_id):
    uniform = get_object_or_404(Uniform, id=uniform_id)
    uniform.delete()
    messages.success(request, "Uniform deleted successfully.")
    return redirect('manage_uniforms')

def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, "User details updated successfully.")
        return redirect('manage_users')  # Adjust URL name if necessary
    return render(request, 'edit_user.html', {'user': user})

def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"{user.username} has been deactivated.")
    return redirect('manage_users')  # Adjust URL name if necessary

def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.username} has been activated.")
    return redirect('manage_users')  # Adjust URL name if necessary


def add_order(request):
    if request.method == "POST":
        # Retrieve order details from the form
        customer_name = request.POST.get('customer_name')  # Admin input for customer name
        payment_method = request.POST.get('payment_method')  # Method like "MPESA" or "CASH"
        payment_reference = request.POST.get('payment_reference', '')  # Optional field

        # Uniform details: Get the selected uniform
        uniform_name = request.POST.get('uniform_name')  # ID of selected uniform
        category = request.POST.get('category')  # Category of the uniform
        size = request.POST.get('size')  # Size of the uniform
        price = float(request.POST.get('price'))  # Price of the uniform
        quantity = int(request.POST.get('quantity'))  # Quantity of the uniform
        total_price = price * quantity  # Calculate total price

        # Fetch customer (User instance) or create new user based on customer_name
        customer, created = User.objects.get_or_create(username=customer_name)

        # Fetch the uniform by the uniform_id
        uniform = get_object_or_404(Uniform, id=uniform_name)  # This should be the ID of the selected uniform

        # Create the order with valid ForeignKey relationships
        order = Order.objects.create(
            user=customer,
            uniform_name=uniform,  # The actual Uniform object
            category=category,
            size=size,
            price=price,
            quantity=quantity,
            total_price=total_price,
            payment_method=payment_method,
            payment_reference=payment_reference,
        )

        # Success message
        messages.success(request, f"Order #{order.id} for {customer.username} successfully added!")
        return redirect('manage_orders')  # Redirect to order management page

    # For GET requests: Show the order form
    return render(request, 'manage_orders.html')
def update_order_status(request, order_id):
        if request.method == "POST":
            order = get_object_or_404(Order, id=order_id)
            new_status = request.POST['status']
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} updated to {new_status}.")
            return redirect('manage_orders')  # Replace with your orders URL name

def get_uniform_details(request, uniform_id):
    uniform = get_object_or_404(Uniform, id=uniform_id)
    return JsonResponse({
        'category': uniform.category,
        'size': uniform.size,
        'price': str(uniform.price),
    })

