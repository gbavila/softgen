from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('p/', views.Playground.as_view(), name="playground"),
    path('', views.getFiles, name="getFiles"),
    path('submit/', views.SubmitSpecsView.as_view(), name='submit_specs'),
    path('preview/', views.PreviewView.as_view(), name='preview'),
]