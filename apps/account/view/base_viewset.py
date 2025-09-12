# import logging
#
# import pydash
# from django.http import StreamingHttpResponse
# # from django_elasticsearch_dsl_drf.viewsets import BaseDocumentViewSet
# from rest_framework import mixins
# from rest_framework import viewsets, status
# from rest_framework.exceptions import NotFound
# from rest_framework.response import Response
# from rest_framework.settings import api_settings
# from rest_framework.viewsets import GenericViewSet
#
# # from rest_framework_csv import renderers as r
#
# # from devworks_drf.aggregation.base_aggragation import BaseAggregation
# from devworks_drf.form_field_errors import form_errors
# # from devworks_drf.pagination import SearchResultsSetPagination, AggregationPagination
# # from devworks_drf.request_history import RequestHistory
# # from decworks_openapi.endpoint_schema import doc_method
#
# log = logging.getLogger(__name__)
#
#
# class BasicViewSetActions:
#
#     def list(self, request, **kwargs):
#         return super().list(request, **kwargs)
#
#     def retrieve(self, request, pk=None, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         response = Response(
#             {
#                 "success": True,
#                 "result": serializer.data
#             }
#         )
#         return response
#
#     def create(self, request, refresh_serializer=False, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(
#                 {"success": False, "error": form_errors(serializer.errors)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         serializer.save()
#
#         if refresh_serializer:
#             instance = serializer.instance
#             serializer = self.get_serializer(instance)
#         headers = self.get_success_headers(serializer.data)
#         if hasattr(self, "on_success_modify"):
#             self.on_success_modify(
#                 serializer.instance,
#                 action='create'
#             )
#
#         response = Response(
#             {"success": True, "result": serializer.data},
#             status=status.HTTP_201_CREATED,
#             headers=headers
#         )
#         return response
#
#     def update(self, request, *args, data=None, refresh_serializer=False, **kwargs):
#         data = data if data is not None else request.data
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(
#             instance,
#             data=data,
#             partial=partial
#         )
#         if not serializer.is_valid():
#             return Response(
#                 {
#                     "success": False,
#                     "error": form_errors(serializer.errors)
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         serializer.save()
#
#         if refresh_serializer:
#             instance = serializer.instance
#             serializer = self.get_serializer(instance)
#
#         if getattr(instance, '_prefetched_objects_cache', None):
#             instance._prefetched_objects_cache = {}
#         if hasattr(self, "on_success_modify"):
#             self.on_success_modify(
#                 serializer.instance,
#                 action='update'
#             )
#         response = Response(
#             {
#                 "success": True,
#                 "result": serializer.data
#             }
#         )
#         return response
#
#     def partial_update(self, request, *args, **kwargs):
#         kwargs['partial'] = True
#         return self.update(request, *args, **kwargs)
#
#     def destroy(self, request, pk=None, **kwargs):
#         instance = self.get_object()
#
#         if hasattr(self, "on_success_modify"):
#             self.on_success_modify(instance, action="delete")
#
#         instance.delete()
#
#         response = Response({"success": True, "result": {}})
#         return response
#
#
# class CommonViewSet(BasicViewSetActions, viewsets.ModelViewSet):
#     # pagination_class = SearchResultsSetPagination
#     pass
#
