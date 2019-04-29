from django.urls import path
from . import views

app_name = 'circles' 

urlpatterns = [
    path('', views.TopLevelView.as_view(), name='outer'),
    path('person/<int:contact_id>/', views.person_view, name='person'),
    path('person/autocomplete/', views.ContactAutocomplete.as_view(), name='person-autocomplete'),
    path('<int:pk>/', views.CircleView.as_view(), name='detail'),
    path('<int:pk>/add/', views.add_member, name='add-member'),
]
