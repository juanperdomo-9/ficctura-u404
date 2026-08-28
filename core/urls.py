from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.gateway, name='gateway'),
    path('tienda/', views.shop, name='shop'),
    path('s/<slug:section>/', views.coming_soon, name='coming_soon'),
    # Los navegadores piden /favicon.ico directo, más allá de cualquier
    # <link rel="icon"> en el <head> — sin esto, tira 404 en la consola.
    path('favicon.ico', views.favicon, name='favicon'),
]
