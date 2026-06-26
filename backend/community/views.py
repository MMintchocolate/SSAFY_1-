from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Post, Comment
from .serializers import (
    PostListSerializer, PostDetailSerializer,
    PostWriteSerializer, CommentSerializer, MyCommentSerializer,
)

PAGE_SIZE = 5


# ── Posts ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def post_list(request):
    board_type = request.query_params.get('board_type')
    page = int(request.query_params.get('page', 1))

    qs = Post.objects.all()
    if board_type in ('stock', 'free'):
        qs = qs.filter(board_type=board_type)

    total = qs.count()
    start = (page - 1) * PAGE_SIZE
    posts = qs[start: start + PAGE_SIZE]
    serializer = PostListSerializer(posts, many=True)
    return Response({
        'results': serializer.data,
        'count': total,
        'has_next': start + PAGE_SIZE < total,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_create(request):
    serializer = PostWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(author=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.view_count += 1
    post.save(update_fields=['view_count'])
    serializer = PostDetailSerializer(post)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = PostWriteSerializer(post, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Comments ──────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def comment_list(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    serializer = CommentSerializer(post.comments.all(), many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comment_create(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    serializer = CommentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(author=request.user, post=post)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def comment_delete(request, post_pk, pk):
    comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
    if comment.author != request.user:
        return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── My posts / comments ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_posts(request):
    posts = Post.objects.filter(author=request.user)[:30]
    serializer = PostListSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_comments(request):
    comments = Comment.objects.filter(author=request.user).select_related('post')[:30]
    serializer = MyCommentSerializer(comments, many=True)
    return Response(serializer.data)
