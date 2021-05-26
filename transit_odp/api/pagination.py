import rest_framework.pagination
import rest_framework_gis.pagination


class PageNumberPagination(rest_framework.pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class GeoJsonPagination(rest_framework_gis.pagination.GeoJsonPagination):
    page_size = 800
    page_size_query_param = "page_size"
    max_page_size = 10000
