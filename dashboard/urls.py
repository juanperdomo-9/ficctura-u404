from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.resumen, name='resumen'),

    path('categorias/', views.category_list, name='category_list'),
    path('categorias/nueva/', views.category_form, name='category_add'),
    path('categorias/<int:pk>/', views.category_form, name='category_form'),
    path('categorias/<int:pk>/eliminar/', views.category_delete, name='category_delete'),

    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_form, name='product_add'),
    path('productos/<int:pk>/', views.product_form, name='product_form'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),

    path('pedidos/', views.order_list, name='order_list'),
    path('pedidos/<int:pk>/', views.order_detail, name='order_detail'),
    path('pedidos/<int:pk>/estado/', views.order_set_status, name='order_set_status'),

    path('ofertas/', views.offers, name='offers'),
    path('ofertas/banner/', views.offer_banner, name='offer_banner'),
    path('ofertas/descuento/', views.offer_discount, name='offer_discount'),
    path('ofertas/promocion/nueva/', views.promotion_form, name='promotion_add'),
    path('ofertas/promocion/<int:pk>/', views.promotion_form, name='promotion_form'),
    path('ofertas/promocion/<int:pk>/eliminar/', views.promotion_delete, name='promotion_delete'),
]
