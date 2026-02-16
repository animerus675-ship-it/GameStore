from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html")


def shop(request):
    return render(request, "pages/shop.html")


def product_detail(request, slug):
    return render(request, "pages/product_detail.html", {"slug": slug})


def contact(request):
    return render(request, "pages/contact.html")
