from django.shortcuts import render

# Create your views here.


def home_view(request):
    return render(request, 'home/home_view.html')


def admin_view(request):
    return render(request, 'home/admin_view.html')
