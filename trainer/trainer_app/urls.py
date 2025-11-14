from django.urls import path
from . import views

urlpatterns = [
    # Subject CRUD
    path('subjects/create/', views.create_subject, name='create_subject'),
    path('subjects/', views.get_all_subjects, name='get_all_subjects'),
    path('subjects/<int:subject_id>/', views.get_subject_by_id, name='get_subject_by_id'),
    path('subjects/update/<int:subject_id>/', views.update_subject, name='update_subject'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),

    # Trainer CRUD
    path('trainers/', views.get_all_trainers, name='get_all_trainers'),
    path('trainer/create/', views.create_trainer, name='create_trainer'),
    path("trainer/update/<str:trainer_code>/", views.update_trainer_by_code, name="update_trainer_by_code"),
    path('trainer/delete/<str:trainer_code>/', views.delete_trainer, name='delete_trainer'),
    # path('', views.index_page, name='index'),

]
