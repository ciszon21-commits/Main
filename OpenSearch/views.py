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


class AIChatView(LoginRequiredMixin, TemplateView):
    """AI 聊天頁面"""
    template_name = 'OpenSearch/ai_chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's recent chats
        from .models import AIChat
        context['recent_chats'] = AIChat.objects.filter(
            user=self.request.user
        ).order_by('-updated_at')[:20]
        
        # Get current chat if specified
        chat_id = self.request.GET.get('chat_id')
        if chat_id:
            try:
                chat = AIChat.objects.get(id=chat_id, user=self.request.user)
                context['current_chat'] = chat
                context['messages'] = chat.messages.all()
            except AIChat.DoesNotExist:
                pass
        
        # Get available categories for filtering
        try:
            categories = services.get_index_categories()
            context['categories'] = {k: v for k, v in categories.items() if v['count'] > 0}
        except Exception:
            context['categories'] = {}
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class AIChatApiView(LoginRequiredMixin, View):
    """AI 聊天 API 端點"""
    
    def post(self, request):
        """Handle new chat message"""
        from .models import AIChat, AIChatMessage
        from . import ai_services
        
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()
            chat_id = data.get('chat_id')
            indices = data.get('indices', '*')
            
            if not question:
                return JsonResponse({'error': '請輸入問題'}, status=400)
            
            # Get or create chat session
            if chat_id:
                try:
                    chat = AIChat.objects.get(id=chat_id, user=request.user)
                except AIChat.DoesNotExist:
                    return JsonResponse({'error': '找不到對話'}, status=404)
            else:
                # Create new chat with title from first question
                title = question[:100] if len(question) <= 100 else question[:97] + '...'
                chat = AIChat.objects.create(
                    user=request.user,
                    title=title,
                    indices=indices
                )
            
            # Save user message
            user_message = AIChatMessage.objects.create(
                chat=chat,
                role='user',
                content=question
            )
            
            # Call AI service
            result = ai_services.ask_ai(
                question=question,
                user=request.user,
                indices=indices,
                max_retries=3
            )
            
            # Save assistant message
            assistant_message = AIChatMessage.objects.create(
                chat=chat,
                role='assistant',
                content=result['answer'],
                keywords_used=result.get('keywords_used', ''),
                search_count=result.get('search_count', 0),
                retry_count=result.get('retry_count', 0),
                sources=result.get('sources', []),
                prompt_tokens=result.get('metrics', {}).get('prompt_tokens', 0),
                completion_tokens=result.get('metrics', {}).get('completion_tokens', 0),
            )
            
            # Update chat timestamp
            chat.save()  # This triggers auto_now on updated_at
            
            return JsonResponse({
                'success': result['success'],
                'chat_id': chat.id,
                'message_id': assistant_message.id,
                'answer': result['answer'],
                'keywords_used': result.get('keywords_used', ''),
                'search_count': result.get('search_count', 0),
                'retry_count': result.get('retry_count', 0),
                'sources': result.get('sources', []),
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '無效的請求格式'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class AIChatHistoryApiView(LoginRequiredMixin, View):
    """AI 對話歷史 API"""
    
    def get(self, request, chat_id):
        """Get chat history"""
        from .models import AIChat
        
        try:
            chat = AIChat.objects.get(id=chat_id, user=request.user)
            messages = []
            for msg in chat.messages.all():
                messages.append({
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'keywords_used': msg.keywords_used,
                    'search_count': msg.search_count,
                    'retry_count': msg.retry_count,
                    'sources': msg.sources,
                    'created_at': msg.created_at.isoformat(),
                })
            
            return JsonResponse({
                'chat_id': chat.id,
                'title': chat.title,
                'indices': chat.indices,
                'messages': messages,
            })
            
        except AIChat.DoesNotExist:
            return JsonResponse({'error': '找不到對話'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def delete(self, request, chat_id):
        """Delete chat"""
        from .models import AIChat
        
        try:
            chat = AIChat.objects.get(id=chat_id, user=request.user)
            chat.delete()
            return JsonResponse({'success': True})
        except AIChat.DoesNotExist:
            return JsonResponse({'error': '找不到對話'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

