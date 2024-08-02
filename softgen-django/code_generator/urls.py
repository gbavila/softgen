from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('testes/', views.Playground.as_view(), name="Playground"),
    path('openai/', views.OpenAIPlayground.as_view(), name="OpenAIPlayground"),
    path('git/', views.GitPlayground.as_view(), name="GitPlayground"),
    path('vercel/', views.VercelPlayground.as_view(), name="VercelPlayground"),
    path('', views.getFiles, name="getFiles"),
    path('submit/', views.SubmitSpecsView.as_view(), name='submit_specs'),
    path('preview/', views.PreviewView.as_view(), name='preview'),
    path('status/', views.CheckGenerationView.as_view(), name='check-generation'),
    path('delete/', views.DeleteSoftwareView.as_view(), name='delete-software'),
    path('update/', views.UpdateSoftwareView.as_view(), name='update-software'),
]