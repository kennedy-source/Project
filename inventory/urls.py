from django.urls import path
from . import views
from .views import login_view
from .views import edit_user, deactivate_user, activate_user, add_order, update_order_status

urlpatterns = [
    # Root URL redirects based on authentication
    path('', views.redirect_home, name='redirect_home'),  # Root path

    # Other URL patterns
    path('home/', views.home, name='admin_home'),  # Admin home route
    path('add_uniform/', views.add_uniform, name='add_uniform'),
    path('place_order/<int:uniform_id>/', views.place_order, name='place_order'),
    path('customer/', views.customer_page, name='customer_page'),  # Customer page route
    path('analytics/', views.sales_analytics, name='sales_analytics'),
    path('inventory_alert/', views.low_stock_alert, name='inventory_alert'),
    path('login/', login_view, name='login'),  # Login page route
    path('manage_users/', views.manage_users, name='manage_users'),
    path('download_inventory_report/', views.download_inventory_report, name='download_inventory_report'),
    path('search/', views.search_uniform, name='search_uniform'),
    path('edit/<int:uniform_id>/', views.edit_uniform, name='edit_uniform'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('orders/', views.manage_orders, name='manage_orders'),
    path('profile/', views.profile, name='profile'),
    path('order_history/', views.order_history, name='order_history'),
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:uniform_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('manage_uniforms/', views.manage_uniforms, name='manage_uniforms'),
    path('delete_uniform/<int:uniform_id>/', views.delete_uniform, name='delete_uniform'),
    path('edit_user/<int:user_id>/', edit_user, name='edit_user'),
    path('deactivate_user/<int:user_id>/', deactivate_user, name='deactivate_user'),
    path('activate_user/<int:user_id>/', activate_user, name='activate_user'),
   path('orders/add/', add_order, name='add_order'),
    path('orders/update_status/<int:order_id>/', update_order_status, name='update_order_status'),
    path('get_uniform_details/<int:uniform_id>/', views.get_uniform_details, name='get_uniform_details'),
]
