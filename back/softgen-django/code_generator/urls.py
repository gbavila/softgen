from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('playground/', views.playground, name="playground"),
    path('', views.getCode, name="getCode"),
    path('add/', views.addCode),
]