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

    def get_raw_search_terms(self, request, search_param=None):
        value = request.query_params.get(search_param or self.search_param, '')

        field = CharField(trim_whitespace=False, allow_blank=True)
        cleaned_value = field.run_validation(value)
        cleaned_value = cleaned_value.replace(',', '|')
        query = search_smart_split(cleaned_value)

        def to_raw(q):
            def quote(i): return f"'{i.strip()}'"
            def parentheses(i): return f"({i.strip()})"
            def or_join(i): return ' | '.join(i)
            def and_join(i): return ' & '.join(i)
            def is_multiple(i): return ' ' in i
            def multiple_query(i): return parentheses(and_join(map(quote, i.split(' '))))

            q = ' '.join(query)
            q = q.split('|')
            q = or_join([
                multiple_query(i) if is_multiple(i) else quote(i) for i in q
            ])
            return q

        if query:
            query = to_raw(query)
            return SearchQuery(query, search_type='raw')

    def filter_queryset(self, request, queryset, view, distinct=True):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_raw_search_terms(request, search_param=getattr(view, 'search_param', 'search'))
        exclude_terms = self.get_raw_search_terms(request, search_param='exclude')

        if not search_fields or (not search_terms and not exclude_terms):
            return queryset

        if not hasattr(queryset.model, 'search_vector'):
            vector = SearchVector(*search_fields)
            queryset = queryset.annotate(search_vector=vector)

        if search_terms:
            queryset = queryset.filter(search_vector=search_terms)
        if exclude_terms:
            queryset = queryset.exclude(search_vector=exclude_terms)

        if distinct:
            return queryset.distinct()
        return queryset
