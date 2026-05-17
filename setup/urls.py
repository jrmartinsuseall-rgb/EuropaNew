from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home_redirect(request):
    return redirect('core:home')

def root_redirect(request):
    return redirect('core:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('cadastros/', include('cadastros.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('servicos/',   include('servicos.urls')),
    path('estoque/',    include('estoque.urls')),
    path('vendas/',     include('vendas.urls')),
    path('home/', home_redirect, name='home'),
    path('', root_redirect),
]
