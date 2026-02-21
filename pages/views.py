from django.shortcuts import render

from catalog.views import shop as catalog_shop


def home(request):
    return render(request, "pages/home.html")


def shop(request):
    return catalog_shop(request)


def product_detail(request, slug):
    return render(request, "pages/product_detail.html", {"slug": slug})


def contact(request):
    return render(request, "pages/contact.html")
