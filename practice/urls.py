from django.urls import path

from . import views

app_name = 'practice'

urlpatterns = [
    path('practice/', views.practice_index, name='practice_index'),
    path('practice/start/<int:set_id>/', views.practice_start, name='practice_start'),
    path('practice/<int:session_id>/', views.practice_session, name='practice_session'),
    path('history/', views.history, name='history'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Question sets CRUD
    path('sets/', views.question_set_list, name='question_set_list'),
    path('sets/create/', views.question_set_create, name='question_set_create'),
    path('sets/<int:pk>/edit/', views.question_set_edit, name='question_set_edit'),
    path('sets/<int:pk>/delete/', views.question_set_delete, name='question_set_delete'),
    # Questions CRUD (within a set)
    path('sets/<int:set_id>/questions/', views.question_list, name='question_list'),
    path('sets/<int:set_id>/questions/add/', views.question_create, name='question_create'),
    path('sets/<int:set_id>/questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('sets/<int:set_id>/questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
]
