from django.contrib.postgres.search import SearchQuery, SearchVector

from rest_framework.filters import SearchFilter


class FullTextSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        fields = super().get_search_fields(view, request)
        if fields:
            prefixes = ''.join(self.lookup_prefixes.keys())
            fields = list(map(lambda i: i.strip(prefixes), fields))

        return fields

    def get_search_terms(self, request) -> str:
        query = super().get_search_terms(request)
        if query:
            return SearchQuery(' '.join(query))

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        vector = SearchVector(*search_fields)
        queryset = queryset.annotate(search=vector).filter(search=search_terms)

        return queryset.distinct('id')
