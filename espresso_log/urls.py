from django.urls import path

from . import views

urlpatterns = [
    path("", views.shot_list, name="shot_list"),
    path("shots/<int:pk>/delete/", views.shot_delete, name="shot_delete"),
    path("shots/import/", views.shots_import, name="shots_import"),
    path("shots/export.csv", views.shots_export, name="shots_export"),
    path("predict/", views.predict, name="predict"),
]
