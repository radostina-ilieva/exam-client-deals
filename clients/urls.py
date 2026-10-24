from django.urls import path, include
from clients.views import ClientHomeListView, ClientCreateView, ClientEditView, ClientDeleteView, ClientDetailView
from clients.views import SectorHomeListView, SectorCreateView, SectorEditView, SectorDeleteView, SectorDetailView

app_name = 'clients'
urlpatterns = [
    path('', ClientHomeListView.as_view(), name='client-list'),
    path('create/', ClientCreateView.as_view(), name='client-create'),
    path('<int:pk>/', include([
        path('', ClientDetailView.as_view(), name='client-detail'),
        path('edit/', ClientEditView.as_view(), name='client-edit'),
        path('delete/', ClientDeleteView.as_view(), name='client-delete'),]
    )),


    path('sectors/', SectorHomeListView.as_view(), name='sector-list'),
    path('sectors/create/', SectorCreateView.as_view(), name='sector-create'),

    path('sectors/<int:pk>/', include([
            path('', SectorDetailView.as_view(), name='sector-detail'),
            path('edit/', SectorEditView.as_view(), name='sector-edit'),
            path('delete/', SectorDeleteView.as_view(), name='sector-delete'),
        ]))


]