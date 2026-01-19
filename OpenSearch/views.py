"""
OpenSearch Views
"""
import json
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from . import services
from .models import SearchLog, ClickLog


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page with Google-style search box"""
    template_name = 'OpenSearch/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            categories = services.get_index_categories()
            # Only show categories with data
            active_categories = {k: v for k, v in categories.items() if v['count'] > 0}
            context['categories'] = active_categories
            context['total_docs'] = sum(c['total_docs'] for c in active_categories.values())
        except Exception as e:
            context['error'] = str(e)
            context['categories'] = {}
            context['total_docs'] = 0
        return context


class SearchView(LoginRequiredMixin, TemplateView):
    """Search results page with Google-style display"""
    template_name = 'OpenSearch/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search parameters
        query = self.request.GET.get('q', '')
        indices = self.request.GET.get('indices', '*')
        page = int(self.request.GET.get('page', 1))
        size = 20
        from_ = (page - 1) * size
        sort_by = self.request.GET.get('sort', None)
        date_from = self.request.GET.get('date_from', None)
        date_to = self.request.GET.get('date_to', None)
        
        context['query'] = query
        context['indices'] = indices
        context['current_page'] = page
        context['sort'] = sort_by
        context['date_from'] = date_from
        context['date_to'] = date_to
        
        if query or indices != '*':
            try:
                # Execute search
                response = services.search(
                    query=query,
                    indices=indices,
                    size=size,
                    from_=from_,
                    sort_by=sort_by,
                    date_from=date_from,
                    date_to=date_to
                )
                
                if 'error' in response:
                    context['error'] = response['error']
                    context['results'] = []
                    context['total'] = 0
                else:
                    hits = response.get('hits', {})
                    took = response.get('took', 0)
                    total = hits.get('total', {})
                    if isinstance(total, dict):
                        total_value = total.get('value', 0)
                    else:
                        total_value = total
                    
                    results = []
                    for hit in hits.get('hits', []):
                        source = hit.get('_source', {})
                        highlight = hit.get('highlight', {})
                        index_name = hit.get('_index', '')
                        
                        # Check if this is secret data:
                        # 1. Document has secret=True flag
                        # 2. OR index comes from reviewing_ alias (all reviewing data is sensitive)
                        is_secret = bool(source.get('secret')) or index_name.startswith('reviewing_')
                        
                        # Filter sensitive data for secret documents
                        # Superusers can see full content but it's still marked as secret
                        if is_secret and not self.request.user.is_superuser:
                            # Only keep title, poster, and minimal metadata
                            filtered_source = {
                                'title': source.get('title', ''),
                                'poster': source.get('poster', ''),
                                'dt': source.get('dt', ''),
                                'secret': True,
                            }
                            source = filtered_source
                            highlight = {}  # Clear all highlights for secret data
                        
                        result = {
                            'index': index_name,
                            'id': hit.get('_id', ''),
                            'score': hit.get('_score', 0),
                            'source': source,
                            'highlight': highlight,
                            'is_secret': is_secret,
                            'category': services.get_category_from_index(index_name),
                        }
                        results.append(result)
                    
                    context['results'] = results
                    context['total'] = total_value
                    context['took_seconds'] = round(took / 1000, 2)
                    context['page_count'] = (total_value + size - 1) // size
                    context['has_prev'] = page > 1
                    context['has_next'] = page * size < total_value
                    context['prev_page'] = page - 1
                    context['next_page'] = page + 1
                    
                    # Log the search query
                    if query:
                        try:
                            SearchLog.objects.create(
                                user=self.request.user if self.request.user.is_authenticated else None,
                                query=query,
                                indices=indices,
                                results_count=total_value
                            )
                        except Exception:
                            pass  # Don't let logging errors break search
                    
                    # Get categories for filter sidebar
                    categories = services.get_index_categories()
                    context['categories'] = {k: v for k, v in categories.items() if v['count'] > 0}
                    
            except Exception as e:
                context['error'] = str(e)
                context['results'] = []
                context['total'] = 0
        else:
            context['results'] = []
            context['total'] = 0
            try:
                categories = services.get_index_categories()
                context['categories'] = {k: v for k, v in categories.items() if v['count'] > 0}
            except Exception:
                context['categories'] = {}
        
        return context


class AdvancedSearchView(LoginRequiredMixin, TemplateView):
    """Advanced search with more filters"""
    template_name = 'OpenSearch/advanced.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            categories = services.get_index_categories()
            context['categories'] = {k: v for k, v in categories.items() if v['count'] > 0}
        except Exception as e:
            context['error'] = str(e)
            context['categories'] = {}
        return context


class ApiSearchView(LoginRequiredMixin, View):
    """API endpoint for AJAX search"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        indices = request.GET.get('indices', '*')
        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 20))
        from_ = (page - 1) * size
        
        try:
            response = services.search(
                query=query,
                indices=indices,
                size=size,
                from_=from_
            )
            
            if 'error' in response:
                return JsonResponse({'error': response['error']}, status=500)
            
            hits = response.get('hits', {})
            total = hits.get('total', {})
            if isinstance(total, dict):
                total_value = total.get('value', 0)
            else:
                total_value = total
            
            results = []
            for hit in hits.get('hits', []):
                source = hit.get('_source', {})
                highlight = hit.get('highlight', {})
                index_name = hit.get('_index', '')
                
                # Check if this is secret data:
                # 1. Document has secret=True flag
                # 2. OR index comes from reviewing_ alias (all reviewing data is sensitive)
                is_secret = bool(source.get('secret')) or index_name.startswith('reviewing_')
                
                # Filter sensitive data for secret documents
                # Superusers can see full content but it's still marked as secret
                if is_secret and not request.user.is_superuser:
                    source = {
                        'title': source.get('title', ''),
                        'poster': source.get('poster', ''),
                        'dt': source.get('dt', ''),
                        'secret': True,
                    }
                    highlight = {}
                
                results.append({
                    'index': index_name,
                    'id': hit.get('_id', ''),
                    'score': hit.get('_score', 0),
                    'source': source,
                    'highlight': highlight,
                    'is_secret': is_secret,
                    'category': services.get_category_from_index(index_name),
                })
            
            return JsonResponse({
                'total': total_value,
                'results': results,
                'page': page,
                'size': size,
                'pages': (total_value + size - 1) // size
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogClickView(LoginRequiredMixin, View):
    """API endpoint to log click actions on search results"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            ClickLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                query=data.get('query', ''),
                index_name=data.get('index', ''),
                doc_id=data.get('doc_id', ''),
                title=data.get('title', '')[:500],
                path=data.get('path', '')
            )
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
