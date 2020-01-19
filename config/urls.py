from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView, TemplateView

from app.views import LoginView, SignupView, DestinationListView, DestinationCreateView, DestinationEditView, \
    DestinationDeleteView, UploadView, DestinationHistoryView


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('cabinet/', RedirectView.as_view(pattern_name='destination_list')),
    path('cabinet/login/', LoginView.as_view(), name='login'),
    path('cabinet/signup/', SignupView.as_view(), name='signup'),
    path('cabinet/logout/', LogoutView.as_view(), name='logout'),
    path('cabinet/destinations/', DestinationListView.as_view(), name='destination_list'),
    path('cabinet/destinations/new/<content_type>/', DestinationCreateView.as_view(), name='destination_new'),
    path('cabinet/destinations/<uuid:pk>/', DestinationHistoryView.as_view(), name='destination_history'),
    path('cabinet/destinations/<uuid:pk>/edit/', DestinationEditView.as_view(), name='destination_edit'),
    path('cabinet/destinations/<uuid:pk>/delete/', DestinationDeleteView.as_view(), name='destination_delete'),
    path('upload/<uuid:destination_id>/', csrf_exempt(UploadView.as_view()), name='upload'),
    path('admin/', admin.site.urls, name='admin'),
]
