from django.urls import path
from general.views import DealHomeView

urlpatterns = [
    path('', DealHomeView.as_view(), name='home'),
]
