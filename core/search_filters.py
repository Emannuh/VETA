"""
Filtering, search, and query utilities for VETA Connect
Handles advanced filtering and search capabilities
"""

from django.db.models import Q, F, Count, Avg
from django.core.paginator import Paginator
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import operator
from functools import reduce


class AdvancedFilter:
    """Advanced filtering for querysets"""
    
    def __init__(self, queryset):
        self.queryset = queryset
    
    def filter_by_date_range(
        self,
        field_name: str,
        start_date: datetime,
        end_date: datetime
    ):
        """Filter by date range"""
        return self.queryset.filter(
            **{f'{field_name}__gte': start_date, f'{field_name}__lte': end_date}
        )
    
    def filter_by_status(self, status: str):
        """Filter by status field"""
        return self.queryset.filter(status=status)
    
    def filter_by_multiple_status(self, statuses: List[str]):
        """Filter by multiple status values"""
        q_objects = Q()
        for status in statuses:
            q_objects |= Q(status=status)
        return self.queryset.filter(q_objects)
    
    def filter_by_rating(self, min_rating: float, max_rating: float = 5.0):
        """Filter by rating range"""
        return self.queryset.filter(
            rating__gte=min_rating,
            rating__lte=max_rating
        )
    
    def filter_recent(self, days: int = 7, field_name: str = 'created_at'):
        """Filter to recent items"""
        since = datetime.now() - timedelta(days=days)
        return self.queryset.filter(**{f'{field_name}__gte': since})
    
    def exclude_archived(self):
        """Exclude archived items"""
        return self.queryset.filter(archived=False)
    
    def search(self, search_fields: List[str], query: str):
        """Search across multiple fields"""
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f'{field}__icontains': query})
        return self.queryset.filter(q_objects)


class SearchEngine:
    """Full-text search capabilities"""
    
    def __init__(self, queryset):
        self.queryset = queryset
    
    def search_by_text(self, fields: List[str], query: str, boost_weights: Optional[Dict] = None):
        """Search with weighted field matching"""
        if not query:
            return []
        
        boost_weights = boost_weights or {field: 1 for field in fields}
        
        results = []
        for item in self.queryset:
            score = 0
            query_lower = query.lower()
            
            for field in fields:
                field_value = str(getattr(item, field, '')).lower()
                if query_lower in field_value:
                    # Exact matches get higher score
                    if field_value == query_lower:
                        score += 100 * boost_weights.get(field, 1)
                    # Partial matches
                    elif field_value.startswith(query_lower):
                        score += 50 * boost_weights.get(field, 1)
                    else:
                        score += 10 * boost_weights.get(field, 1)
            
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in results]
    
    def autocomplete(self, field: str, prefix: str, limit: int = 10):
        """Autocomplete suggestions"""
        items = self.queryset.filter(**{f'{field}__istartswith': prefix})
        return list(items.values_list(field, flat=True).distinct()[:limit])


class QueryOptimizer:
    """Optimizes queries to reduce database hits"""
    
    @staticmethod
    def optimize_with_select_related(queryset, relations: List[str]):
        """Add select_related for foreign keys"""
        for relation in relations:
            queryset = queryset.select_related(relation)
        return queryset
    
    @staticmethod
    def optimize_with_prefetch_related(queryset, relations: List[str]):
        """Add prefetch_related for reverse relations"""
        for relation in relations:
            queryset = queryset.prefetch_related(relation)
        return queryset
    
    @staticmethod
    def add_annotations(queryset, annotations: Dict):
        """Add aggregation annotations"""
        return queryset.annotate(**annotations)


class PaginationHelper:
    """Helper for pagination"""
    
    @staticmethod
    def paginate(
        queryset,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List, Dict]:
        """Paginate queryset"""
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        pagination_info = {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'per_page': per_page,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        }
        
        return list(page_obj), pagination_info


class SortingHelper:
    """Helper for sorting"""
    
    ALLOWED_SORT_FIELDS = {
        'created_at': '-created_at',
        'updated_at': '-updated_at',
        'rating': '-rating',
        'title': 'title',
        'name': 'name',
    }
    
    @classmethod
    def get_sort_field(cls, sort_param: str) -> Optional[str]:
        """Get validated sort field"""
        if sort_param.startswith('-'):
            base_field = sort_param[1:]
            if base_field in cls.ALLOWED_SORT_FIELDS:
                return f'-{base_field}'
        
        return cls.ALLOWED_SORT_FIELDS.get(sort_param)
    
    @classmethod
    def apply_sort(cls, queryset, sort_param: str):
        """Apply sorting to queryset"""
        sort_field = cls.get_sort_field(sort_param)
        if sort_field:
            return queryset.order_by(sort_field)
        return queryset


class FilterBuilder:
    """Builds complex filter queries"""
    
    def __init__(self):
        self.filters = []
    
    def add_filter(self, **kwargs):
        """Add filter condition"""
        self.filters.append(Q(**kwargs))
        return self
    
    def add_exclude(self, **kwargs):
        """Add exclude condition"""
        self.filters.append(~Q(**kwargs))
        return self
    
    def add_range_filter(self, field: str, min_val: Any, max_val: Any):
        """Add range filter"""
        self.filters.append(Q(**{f'{field}__gte': min_val, f'{field}__lte': max_val}))
        return self
    
    def add_in_filter(self, field: str, values: List[Any]):
        """Add IN filter"""
        self.filters.append(Q(**{f'{field}__in': values}))
        return self
    
    def add_text_search(self, fields: List[str], query: str):
        """Add text search across fields"""
        q_objects = Q()
        for field in fields:
            q_objects |= Q(**{f'{field}__icontains': query})
        self.filters.append(q_objects)
        return self
    
    def build(self, queryset):
        """Build and apply all filters"""
        if not self.filters:
            return queryset
        
        combined_q = reduce(operator.and_, self.filters)
        return queryset.filter(combined_q)


class AggregationHelper:
    """Helper for aggregations and statistics"""
    
    @staticmethod
    def get_stats(queryset, numeric_field: str) -> Dict:
        """Get statistics for numeric field"""
        stats = queryset.aggregate(
            count=Count(numeric_field),
            average=Avg(numeric_field),
            min_value=Min(numeric_field),
            max_value=Max(numeric_field),
        )
        return stats
    
    @staticmethod
    def get_group_by_stats(queryset, group_field: str, numeric_field: str) -> List[Dict]:
        """Get statistics grouped by field"""
        return list(
            queryset.values(group_field).annotate(
                count=Count(numeric_field),
                average=Avg(numeric_field),
            )
        )


# Import Min, Max for aggregation
from django.db.models import Min, Max
