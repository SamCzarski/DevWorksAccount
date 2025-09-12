from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework import viewsets
# from apps.api.models import AppUser
# from apps.api.serializers import AppUserSerializer



@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def test_view(request):
    return Response({"message": "Hello World!"})




class InitViewSet(APIView):

    def get(self, request):
        return Response("GET hello world!")

    def post(self, request):
        return Response("POST hello world!")

    def put(self, request):
        return Response("PUT hello world!")

    def delete(self, request):
        return Response("DELETE hello world!")




# class AppUserViewSet(viewsets.ModelViewSet):
#     queryset = AppUser.objects.all()
#     serializer_class = AppUserSerializer



