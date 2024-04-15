from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('openai/', views.OpenAIPlayground.as_view(), name="OpenAIPlayground"),
    path('git/', views.GitPlayground.as_view(), name="GitPlayground"),
    path('', views.getFiles, name="getFiles"),
    path('submit/', views.SubmitSpecsView.as_view(), name='submit_specs'),
    path('preview/', views.PreviewView.as_view(), name='preview'),
]