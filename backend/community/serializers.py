from rest_framework import serializers
from .models import Post, Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['post', 'author_name', 'created_at', 'updated_at']


class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'board_type', 'title', 'author_name',
            'created_at', 'view_count', 'comment_count',
        ]
        read_only_fields = ['author_name', 'created_at', 'view_count', 'comment_count']


class PostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'board_type', 'title', 'content', 'author_name',
            'created_at', 'updated_at', 'view_count', 'comments',
        ]
        read_only_fields = ['author_name', 'created_at', 'updated_at', 'view_count', 'comments']


class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'board_type', 'title', 'content']
