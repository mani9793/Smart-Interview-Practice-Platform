from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    # Replace with real views when merging Practice & Question Sets
    path('practice/', views.practice_placeholder, name='practice'),
    path('question-sets/', views.question_sets_placeholder, name='question_sets'),
    path('history/', views.history_placeholder, name='history'),
]
