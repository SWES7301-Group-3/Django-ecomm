from django.shortcuts import render

# Create your views here.
# shop/views.py
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the Bluewave Store 🛒")
