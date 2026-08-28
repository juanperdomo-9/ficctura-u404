from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),

    path('carrito/', views.cart_view, name='cart'),
    path('carrito/estado/', views.cart_state, name='cart_state'),
    path('carrito/sumar/<int:variant_id>/', views.cart_add, name='cart_add'),
    path('carrito/restar/<int:variant_id>/', views.cart_subtract, name='cart_subtract'),
    path('carrito/sacar/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('carrito/vaciar/', views.cart_clear, name='cart_clear'),

    path('checkout/', views.checkout, name='checkout'),
    path('checkout/<int:order_id>/gracias/', views.order_confirmation, name='order_confirmation'),

    # Van al final: son un catch-all de slug, cualquier ruta más
    # específica de arriba tiene que quedar antes de estas dos.
    path('<slug:slug>/', views.product_detail, name='detail'),
    path('<slug:slug>/reservar/', views.reserve_product, name='reserve'),
]
