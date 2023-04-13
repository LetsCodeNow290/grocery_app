from django.shortcuts import render

# Create your views here.


def home_view(request):
    return render(request, 'app_home/home_view.html')


def admin_view(request):
    return render(request, 'app_home/admin_view.html')
