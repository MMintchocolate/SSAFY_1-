from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import RegisterSerializer, UserSerializer, NicknameUpdateSerializer

FRONTEND_URL = 'http://localhost:5173'


def _token_pair(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
        'user':    UserSerializer(user).data,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    return Response(_token_pair(user), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.check_password(password):
        return Response({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({'error': '비활성화된 계정입니다.'}, status=status.HTTP_403_FORBIDDEN)

    return Response(_token_pair(user))


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'refresh 토큰이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        pass
    return Response({'detail': '로그아웃 되었습니다.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def cluster_settings(request):
    user = request.user
    if request.method == 'GET':
        return Response({
            'cluster_eps':         user.cluster_eps,
            'cluster_min_samples': user.cluster_min_samples,
        })
    eps  = request.data.get('cluster_eps')
    mins = request.data.get('cluster_min_samples')
    if eps  is not None:
        user.cluster_eps = round(float(eps), 2)
    if mins is not None:
        user.cluster_min_samples = int(mins)
    user.save(update_fields=['cluster_eps', 'cluster_min_samples'])
    return Response({
        'cluster_eps':         user.cluster_eps,
        'cluster_min_samples': user.cluster_min_samples,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_nickname(request):
    serializer = NicknameUpdateSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    current = request.data.get('current_password', '')
    new_pw  = request.data.get('new_password', '')

    if not request.user.check_password(current):
        return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_pw, request.user)
    except ValidationError as e:
        return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_pw)
    request.user.save()
    return Response({'detail': '비밀번호가 변경되었습니다.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_google_password(request):
    """
    현재 비밀번호 확인 후 본인 이메일로 재설정 링크 발송.
    body: { "current_password": "..." }
    """
    current_password = request.data.get('current_password', '')
    if not current_password:
        return Response({'error': '현재 비밀번호를 입력해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(current_password):
        return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.email:
        return Response({'error': '등록된 이메일이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    try:
        send_mail(
            subject='[SafeFinance] 비밀번호 재설정 안내',
            message=(
                f'안녕하세요, {user.nickname or user.username}님.\n\n'
                f'아래 재설정 코드를 복사하여 비밀번호 변경 페이지에 입력해 주세요.\n'
                f'코드는 발급 후 1시간 동안 유효합니다.\n\n'
                f'━━━━━━━━━━━━━━━━━━━━\n'
                f'UID   : {uid}\n'
                f'TOKEN : {token}\n'
                f'━━━━━━━━━━━━━━━━━━━━\n\n'
                f'[비밀번호 변경 방법]\n'
                f'브라우저 주소창에 직접 입력하세요:\n'
                f'localhost:5173/reset-password\n\n'
                f'본인이 요청하지 않았다면 이 메일을 무시하세요.'
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({'error': f'메일 발송에 실패했습니다: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'detail': f'{user.email}로 재설정 코드를 발송했습니다.', 'email': user.email})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    이메일 링크 클릭 후 새 비밀번호 저장.
    body: { "uid": "...", "token": "...", "new_password": "..." }
    """
    uid          = request.data.get('uid', '')
    token        = request.data.get('token', '')
    new_password = request.data.get('new_password', '')

    if not uid or not token or not new_password:
        return Response({'error': 'uid, token, new_password 모두 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pk   = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'error': '유효하지 않은 링크입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({'error': '링크가 만료되었거나 유효하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'detail': '비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.'})