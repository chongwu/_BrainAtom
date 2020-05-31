from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    # path('', views.bot, name='bot'),
    path('get-message', views.set_webhook, name='get_message')
]