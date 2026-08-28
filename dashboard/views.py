from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import BrandPromotion, Category, Order, PaymentDiscount, Product, Promotion

from .decorators import staff_required
from .forms import (
    BrandPromotionForm, CategoryForm, PaymentDiscountForm, ProductForm,
    ProductImageFormSet, ProductVariantFormSet, PromotionForm,
)


def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:resumen')

    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', ''),
            password=request.POST.get('password', ''),
        )
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get('next') or 'dashboard:resumen')
        error = 'Usuario o contraseña incorrectos.'

    return render(request, 'dashboard/login.html', {'error': error})


@staff_required
def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


@staff_required
def resumen(request):
    brand = request.brand
    context = {
        'total_productos': Product.objects.filter(brand=brand).count(),
        'total_categorias': Category.objects.filter(brand=brand).count(),
        'pedidos_pendientes': Order.objects.filter(brand=brand, status=Order.Status.PENDING).count(),
        'pedidos_recientes': Order.objects.filter(brand=brand).order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/resumen.html', context)


# ==========================================================
# CATEGORÍAS
# ==========================================================

@staff_required
def category_list(request):
    categories = Category.objects.filter(brand=request.brand)
    return render(request, 'dashboard/category_list.html', {'categories': categories})


@staff_required
def category_form(request, pk=None):
    instance = get_object_or_404(Category, pk=pk, brand=request.brand) if pk else None

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=instance)
        if form.is_valid():
            # La marca la elige el form (pedido del usuario, 13/8) — si
            # la cambian a la otra marca, la categoría pasa a listarse
            # en el panel de esa otra marca, no en este.
            form.save()
            messages.success(request, 'Categoría guardada.')
            return redirect('dashboard:category_list')
    else:
        form = CategoryForm(instance=instance, initial={'brand': request.brand})

    return render(request, 'dashboard/category_form.html', {'form': form, 'instance': instance})


@staff_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, brand=request.brand)
    category.delete()
    messages.success(request, 'Categoría eliminada.')
    return redirect('dashboard:category_list')


# ==========================================================
# PRODUCTOS — el editor grande vive acá (product_form)
# ==========================================================

def _reset_extra_row_initial(variant_formset, image_formset):
    """Bug real (13/8): ProductVariant.color tiene default="Blanco" a
    nivel modelo — cualquier instancia en blanco (las filas EXTRA, sin
    producto guardado atrás) arranca con ese "Blanco" ya cargado en su
    initial. Eso rompe dos cosas: el JS de agrupación por color (todas
    las filas libres caían en la tarjeta "Blanco"), y la validación:
    Django recalcula el initial de cada form CADA VEZ que se
    reconstruye el formset — también en el POST, no solo al pintar la
    página — así que si acá no se pisa initial['color'] a '' en las
    DOS ramas (GET y POST), has_changed() ve "" (lo que mandó el
    navegador en una fila que el usuario nunca tocó) contra "Blanco"
    (el initial real del modelo) => la marca como "cambiada" => exige
    size/color obligatorios en las 12 filas libres => el guardado
    entero explota aunque el usuario solo haya llenado 1.
    Mismo motivo para hex_color, pero al revés: un <input type="color">
    JAMÁS manda vacío (el navegador siempre manda un hex, default
    #000000), así que ahí el initial se pisa a ese mismo valor en vez
    de a ''.
    Se aplica solo a las filas SIN pk — las que sí tienen un producto
    guardado atrás mantienen su color real.
    """
    for vform in variant_formset.forms:
        if not vform.instance.pk:
            vform.initial['color'] = ''
            vform.initial['hex_color'] = '#000000'
    for iform in image_formset.forms:
        if not iform.instance.pk:
            iform.initial['color'] = ''


@staff_required
def product_list(request):
    products = Product.objects.filter(brand=request.brand).select_related('category')
    return render(request, 'dashboard/product_list.html', {'products': products})


@staff_required
def product_form(request, pk=None):
    """
    Alta/edición de producto + el editor unificado "Colores, talles y
    fotos" (ver static/js/product-panel.js) — versión simplificada del
    patrón de Las Manolas: NO clona el empty_form (ahí está el bug de
    TOTAL_FORMS que pagaron en ese proyecto), usa `extra` fijo en los
    formsets y el JS solo AGRUPA visualmente las filas reales que
    Django ya renderizó. Django solo ve POST de formsets normales al
    final, no sabe que hubo un editor "por color" del otro lado.
    """
    instance = get_object_or_404(Product, pk=pk, brand=request.brand) if pk else None

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=instance, brand=request.brand)
        variant_formset = ProductVariantFormSet(request.POST, instance=instance or Product(brand=request.brand))
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=instance or Product(brand=request.brand))
        _reset_extra_row_initial(variant_formset, image_formset)

        if form.is_valid():
            product = form.save(commit=False)
            product.brand = request.brand
            product.save()

            variant_formset.instance = product
            image_formset.instance = product

            if variant_formset.is_valid() and image_formset.is_valid():
                variant_formset.save()
                image_formset.save()
                messages.success(request, 'Producto guardado.')
                return redirect('dashboard:product_form', pk=product.pk)
    else:
        form = ProductForm(instance=instance, brand=request.brand)
        variant_formset = ProductVariantFormSet(instance=instance)
        image_formset = ProductImageFormSet(instance=instance)
        _reset_extra_row_initial(variant_formset, image_formset)

    return render(request, 'dashboard/product_form.html', {
        'form': form,
        'instance': instance,
        'variant_formset': variant_formset,
        'image_formset': image_formset,
    })


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, brand=request.brand)
    product.delete()
    messages.success(request, 'Producto eliminado.')
    return redirect('dashboard:product_list')


# ==========================================================
# PEDIDOS
# ==========================================================

@staff_required
def order_list(request):
    orders = Order.objects.filter(brand=request.brand).order_by('-created_at')

    status = request.GET.get('status')
    if status in Order.Status.values:
        orders = orders.filter(status=status)

    return render(request, 'dashboard/order_list.html', {
        'orders': orders,
        'status_choices': Order.Status.choices,
        'active_status': status,
    })


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, brand=request.brand)
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
        'status_choices': Order.Status.choices,
    })


@staff_required
@require_POST
def order_set_status(request, pk):
    order = get_object_or_404(Order, pk=pk, brand=request.brand)
    new_status = request.POST.get('status')
    if new_status in Order.Status.values:
        order.status = new_status
        order.save(update_fields=['status'])
        messages.success(request, 'Estado actualizado.')
    return redirect('dashboard:order_detail', pk=order.pk)


# ==========================================================
# OFERTAS — antes esta sección del sidebar linkeaba a /admin/ (pedido
# del usuario, 28/8: que NO vaya ahí). BrandPromotion y PaymentDiscount
# son un solo renglón POR MARCA (unique=True en el modelo) — no hay
# "lista", se edita directo esa única fila; Promotion (3x2, etc.) sí es
# una lista de verdad, con su propio alta/edición/borrado.
# ==========================================================

@staff_required
def offers(request):
    brand_promo, _ = BrandPromotion.objects.get_or_create(brand=request.brand)
    payment_discount, _ = PaymentDiscount.objects.get_or_create(brand=request.brand)
    promotions = Promotion.objects.filter(brand=request.brand)

    return render(request, 'dashboard/offers.html', {
        'banner_form': BrandPromotionForm(instance=brand_promo, brand=request.brand, prefix='banner'),
        'discount_form': PaymentDiscountForm(instance=payment_discount, prefix='descuento'),
        'promotions': promotions,
    })


@staff_required
@require_POST
def offer_banner(request):
    brand_promo, _ = BrandPromotion.objects.get_or_create(brand=request.brand)
    form = BrandPromotionForm(request.POST, instance=brand_promo, brand=request.brand, prefix='banner')
    if form.is_valid():
        form.save()
        messages.success(request, 'Banner de marca actualizado.')
    else:
        messages.error(request, f'No se pudo guardar el banner: {form.errors.as_text()}')
    return redirect('dashboard:offers')


@staff_required
@require_POST
def offer_discount(request):
    payment_discount, _ = PaymentDiscount.objects.get_or_create(brand=request.brand)
    form = PaymentDiscountForm(request.POST, instance=payment_discount, prefix='descuento')
    if form.is_valid():
        form.save()
        messages.success(request, 'Descuento por medio de pago actualizado.')
    else:
        messages.error(request, f'No se pudo guardar el descuento: {form.errors.as_text()}')
    return redirect('dashboard:offers')


@staff_required
def promotion_form(request, pk=None):
    instance = get_object_or_404(Promotion, pk=pk, brand=request.brand) if pk else None

    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=instance, brand=request.brand)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.brand = request.brand
            promo.save()
            messages.success(request, 'Promoción guardada.')
            return redirect('dashboard:offers')
    else:
        form = PromotionForm(instance=instance, brand=request.brand)

    return render(request, 'dashboard/promotion_form.html', {'form': form, 'instance': instance})


@staff_required
@require_POST
def promotion_delete(request, pk):
    promo = get_object_or_404(Promotion, pk=pk, brand=request.brand)
    promo.delete()
    messages.success(request, 'Promoción eliminada.')
    return redirect('dashboard:offers')
