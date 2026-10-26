from django.urls import include, path

from pricing import views

app_name = 'pricing'

urlpatterns = [
    path('', views.PricingHomeView.as_view(), name='home'),

    # Years
    path('years/', views.PricingYearListView.as_view(), name='year-list'),
    path('years/create/', views.PricingYearCreateView.as_view(), name='year-create'),
    path('years/<int:pk>/', include([
        path('', views.PricingYearDetailView.as_view(), name='year-detail'),
        path('delete/', views.PricingYearDeleteView.as_view(), name='year-delete'),
        path('coefficients/', views.YearCoefficientsView.as_view(), name='year-coefficients'),
    ])),

    # Channels
    path('channels/', views.ChannelListView.as_view(), name='channel-list'),
    path('channels/create/', views.ChannelCreateView.as_view(), name='channel-create'),
    path('channels/<int:pk>/', include([
        path('edit/', views.ChannelEditView.as_view(), name='channel-edit'),
        path('delete/', views.ChannelDeleteView.as_view(), name='channel-delete'),
    ])),

    # Target groups
    path('target-groups/', views.TargetGroupListView.as_view(), name='group-list'),
    path('target-groups/create/', views.TargetGroupCreateView.as_view(), name='group-create'),
    path('target-groups/<int:pk>/', include([
        path('', views.TargetGroupDetailView.as_view(), name='group-detail'),
        path('edit/', views.TargetGroupEditView.as_view(), name='group-edit'),
        path('delete/', views.TargetGroupDeleteView.as_view(), name='group-delete'),
    ])),

    # Prices
    path('prices/', views.TargetGroupPriceListView.as_view(), name='price-list'),
    path('prices/create/', views.TargetGroupPriceCreateView.as_view(), name='price-create'),
    path('prices/<int:pk>/', include([
        path('edit/', views.TargetGroupPriceEditView.as_view(), name='price-edit'),
        path('delete/', views.TargetGroupPriceDeleteView.as_view(), name='price-delete'),
    ])),

    # Index bands
    path('index-bands/', views.IndexBandListView.as_view(), name='band-list'),
    path('index-bands/create/', views.IndexBandCreateView.as_view(), name='band-create'),
    path('index-bands/<int:pk>/delete/', views.IndexBandDeleteView.as_view(), name='band-delete'),

    # Calculator
    path('calculator/', views.PriceCalculatorView.as_view(), name='calculator'),
]
