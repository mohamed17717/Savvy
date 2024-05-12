from django.contrib.postgres.search import SearchQuery, SearchVector

from rest_framework.filters import SearchFilter, search_smart_split
from rest_framework.fields import CharField


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

    def get_exclude_terms(self, request) -> str:
        value = request.query_params.get('exclude', '')
        field = CharField(trim_whitespace=False, allow_blank=True)
        cleaned_value = field.run_validation(value)
        query = search_smart_split(cleaned_value)

        if query:
            return SearchQuery(' '.join(query))

    def filter_queryset(self, request, queryset, view, distinct=True):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)
        exclude_terms = self.get_exclude_terms(request)

        if not search_fields or (not search_terms and not exclude_terms):
            return queryset

        vector = SearchVector(*search_fields)
        queryset = queryset.annotate(search=vector)
        if search_terms:
            queryset = queryset.filter(search=search_terms)
        elif exclude_terms:
            queryset = queryset.exclude(search=exclude_terms)

        if distinct:
            return queryset.distinct('id')
        return queryset
