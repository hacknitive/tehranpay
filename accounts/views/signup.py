from rest_framework import generics, status
from rest_framework.response import Response
from ..serializers import SignupSerializer

from rest_framework.permissions import AllowAny, IsAuthenticated

HTTP_201_CREATED = status.HTTP_201_CREATED


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            {
                "statusCode": HTTP_201_CREATED,
                "message": "Operation succeeded.",
                "error": None,
                "data": serializer.data,
            },
            status=HTTP_201_CREATED,
            headers=headers,
        )
