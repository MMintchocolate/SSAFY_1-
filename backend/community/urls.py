from django.urls import path
from . import views

urlpatterns = [
    path('posts/',                                views.post_list,      name='post-list'),
    path('posts/create/',                         views.post_create,    name='post-create'),
    path('posts/<int:pk>/',                       views.post_detail,    name='post-detail'),
    path('posts/<int:pk>/update/',                views.post_update,    name='post-update'),
    path('posts/<int:pk>/delete/',                views.post_delete,    name='post-delete'),
    path('posts/<int:post_pk>/comments/',         views.comment_list,   name='comment-list'),
    path('posts/<int:post_pk>/comments/create/',  views.comment_create, name='comment-create'),
    path('posts/<int:post_pk>/comments/<int:pk>/delete/', views.comment_delete, name='comment-delete'),
    path('my/posts/',    views.my_posts,    name='my-posts'),
    path('my/comments/', views.my_comments, name='my-comments'),
]
