from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='homepage'),
    path('register/', views.register_function, name='register_function'),
    path('trigger/', views.trigger_dispatch, name='trigger_dispatch'),
    path('result/<str:task_id>',views.check_result,name='check_result'),
    path('loadtest/',views.load_test,name='loadtest')
]
