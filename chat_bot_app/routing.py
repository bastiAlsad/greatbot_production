from django.urls import path
from . import views, openAi
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView


urlpatterns = [
    #favivon
    path('favicon.ico', RedirectView.as_view(url='static/favicon.ico')),
    
    path("logout/", views.logout_view, name="logout"),
    #path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path("hub/", views.home, name="home"),
    path("hub/create-customer/", views.create_customer, name="create_customer"),
    path("create-customer/", views.create_customer, name="create_customer"),
    path("edit-customer/<int:id>/", views.edit_customer, name="edit_customer"),
    path("hub/edit-customer/<int:id>/", views.edit_customer, name="edit_customer"),
    path('update_customer/', views.update_customer, name='update_customer'),
    path('hub/update_customer/', views.update_customer, name='update_customer'),
    path('hub/delete-customer/<int:id>/', views.delete_customer, name='update_customer'),
    path('delete-customer/<int:id>/', views.delete_customer, name='update_customer'),
    

    path("api/<str:partner>/assistant-chat/", openAi.chatApplication, name = "assistant_chat"),
    path("api/<str:partner>/assistant-chat/getapiregistrationtoken", openAi.get_api_registration_token, name = "token"),
    path("api/<str:partner>/assistant-chat/sendmessage/", openAi.chatApplication, name = "assistant_chat"),
    path('api/<str:partner>/assistant-chat/saveuserdata/', openAi.save_user_data, name='saveUserData'),
    path('api/<str:partner>/dynamic-css/', views.dynamic_css, name='dynamic_css'),
    path('api/<str:partner>/dynamic-js/', views.dynamic_js, name='dynamic_js'),
]