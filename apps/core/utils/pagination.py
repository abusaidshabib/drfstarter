from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 10  # default if not provided by request
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request):
        try:
            page_size = int(request.query_params.get(
                self.page_size_query_param, self.page_size))
            return min(page_size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size


def custom_array_pagination(data, page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    return data[start:end], len(data)
