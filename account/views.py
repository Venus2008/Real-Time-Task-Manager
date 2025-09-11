import token
from account.models import User
from account.serializers import UserCreateSerializer,UserMeSerializer,SetPasswordSerializer,AdminSignupSerializer
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from account.permissions import IsAdminOrManager,IsAdmin
from .utils import make_password_setup_link, decode_uid
User = get_user_model()
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes




class AddUserView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAdminOrManager]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]
        email = serializer.validated_data["email"]
        name = serializer.validated_data["name"]

        if User.objects.filter(email=email).exists():
            return Response({"detail": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        creator_role = request.user.role
        if creator_role == "MANAGER" and role != "EMPLOYEE":
            return Response({"detail": "Managers can create EMPLOYEE only."}, status=status.HTTP_403_FORBIDDEN)
        
        if creator_role == "ADMIN" and role == "ADMIN" :
            return Response({"detail": "Admin cannot create another Admin."}, status=status.HTTP_403_FORBIDDEN)

        user = User.objects.create_user(
            email=email,
            name=name,
            role=role,
            password=None,      
            is_active=False,
            created_by=request.user
        )
        link = make_password_setup_link(user)

        subject = "Set up your account - Real Time Task Manager"
        body = (
            f"Hi {user.name},\n\n"
            f"An account was created for you in Real Time Task Manager.\n\n"
            f"Please set your password using the link below:\n\n{link}\n\n"
            f"If you didn't expect this, ignore this email."
        )
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        print("UID:", uidb64)
        print("Token:", token)
        return Response({
            "message": "User created. Password setup email sent.",
            "created_by": {
                "id": request.user.id,
                "email": request.user.email,
                "name": request.user.name,
            },
            "user": UserMeSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class SetPasswordView(APIView):
    authentication_classes=[]
    permission_classes=[]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        try:
            uid = decode_uid(uidb64)
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Password set successfully. Account active.",
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
            "user": UserMeSerializer(user).data
        }, status=status.HTTP_200_OK)

class AdminSignupView(APIView):
    authentication_classes = []  # No auth required for first admin signup
    permission_classes = []      # Public for first time only

    def post(self, request):
        # Check if an admin already exists
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "Admin already exists. Please log in instead."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force role = ADMIN
        user = serializer.save(role="ADMIN", is_active=True)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            "message": "Admin account created successfully.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(access)
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    authentication_classes=[]
    permission_classes=[]

    def post(self,request):
        email=request.data.get("email")
        password=request.data.get("password")

        if not email or not password:
            return Response({"detail":"Email and Password are required"},status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            return Response({"detail": "Invalid credentials"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({"detail": "Account inactive. Please complete password setup."}, status=status.HTTP_403_FORBIDDEN)
        
        refresh=RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
            },"user": UserMeSerializer(user).data,
            },status=status.HTTP_200_OK,
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]  

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  
            return Response(
                {"message": "Logged out successfully"},status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {"error": "Invalid or expired token"},status=status.HTTP_400_BAD_REQUEST,)



