from django.urls import path, include

from deals.views import OfferListView, OfferCreateView, OfferDetailView, OfferEditView, OfferDeleteView

app_name = 'deals'

urlpatterns = [
    path('', OfferListView.as_view(), name='offer-list'),
    path('create/', OfferCreateView.as_view(), name='offer-create'),
    path('<int:pk>/', include([
        path('', OfferDetailView.as_view(), name='offer-detail'),
        path('edit/', OfferEditView.as_view(), name='offer-edit'),
        path('delete/', OfferDeleteView.as_view(), name='offer-delete'), ]
    )),
]