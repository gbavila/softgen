from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('playground/', views.Playground.as_view(), name="playground"),
    path('', views.getCode, name="getCode"),
    path('add/', views.addCode),
    path('submit/', views.SubmitSpecsView.as_view(), name='submit_specs'),
]