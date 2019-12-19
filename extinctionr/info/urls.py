from django.urls import include, path

from . import views

app_name = 'extinctionr.info'

urlpatterns = [
    path('pr/', views.PRListView.as_view(), name='pr-list'),
    path('pr/<str:slug>', views.PRDetailView.as_view(), name='pr-detail'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('contact', views.ContactView.as_view(), name="contact"),
    path('groups/', views.list_chapters, name='groups'),
    path('', views.InfoView.as_view(), kwargs={'page': 'home'}, name='index'),
    path('<path:page>', views.InfoView.as_view(), name='page'),
]
