from django.contrib import admin
from .models import Bid, Committee, BidCommittee, Question, BidFile, FileDownloadLog


class QuestionInline(admin.TabularInline):
    """問答記錄內嵌管理"""
    model = Question
    extra = 1
    fields = ['question', 'answer', 'reference', 'order']


class BidCommitteeInline(admin.TabularInline):
    """標案委員內嵌管理"""
    model = BidCommittee
    extra = 1
    autocomplete_fields = ['committee']


class BidFileInline(admin.TabularInline):
    """標案文件內嵌管理"""
    model = BidFile
    extra = 0
    fields = ['filename', 'description', 'uploaded_by', 'uploaded_at', 'get_download_count']
    readonly_fields = ['uploaded_at', 'get_download_count']
    
    def get_download_count(self, obj):
        return obj.get_download_count()
    get_download_count.short_description = '下載次數'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """標案管理"""
    list_display = ['name', 'bid_number', 'bid_date', 'status', 'get_committee_count', 'created_by']
    list_filter = ['status', 'bid_date']
    search_fields = ['name', 'bid_number', 'description']
    date_hierarchy = 'bid_date'
    inlines = [BidCommitteeInline, BidFileInline]
    
    def get_committee_count(self, obj):
        return obj.get_committee_count()
    get_committee_count.short_description = '委員數'


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    """評審委員管理"""
    list_display = ['name', 'organization', 'specialty', 'get_question_count']
    search_fields = ['name', 'organization', 'specialty']
    list_filter = ['organization']
    
    def get_question_count(self, obj):
        return obj.get_question_count()
    get_question_count.short_description = '問答數'


@admin.register(BidCommittee)
class BidCommitteeAdmin(admin.ModelAdmin):
    """標案委員關聯管理"""
    list_display = ['bid', 'committee', 'get_question_count']
    list_filter = ['bid']
    autocomplete_fields = ['bid', 'committee']
    inlines = [QuestionInline]
    
    def get_question_count(self, obj):
        return obj.get_question_count()
    get_question_count.short_description = '問答數'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """問答記錄管理"""
    list_display = ['get_bid_name', 'get_committee_name', 'question_preview', 'created_at']
    list_filter = ['bid_committee__bid', 'bid_committee__committee']
    search_fields = ['question', 'answer', 'reference']
    
    def get_bid_name(self, obj):
        return obj.bid_committee.bid.name
    get_bid_name.short_description = '標案'
    
    def get_committee_name(self, obj):
        return obj.bid_committee.committee.name
    get_committee_name.short_description = '委員'
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = '提問內容'


@admin.register(BidFile)
class BidFileAdmin(admin.ModelAdmin):
    """標案文件管理"""
    list_display = ['filename', 'bid', 'uploaded_by', 'uploaded_at', 'get_download_count']
    list_filter = ['bid', 'uploaded_at']
    search_fields = ['filename', 'description']
    
    def get_download_count(self, obj):
        return obj.get_download_count()
    get_download_count.short_description = '下載次數'


@admin.register(FileDownloadLog)
class FileDownloadLogAdmin(admin.ModelAdmin):
    """下載記錄管理"""
    list_display = ['file', 'downloaded_by', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at', 'file__bid']
    search_fields = ['file__filename', 'downloaded_by__username']
    readonly_fields = ['file', 'downloaded_by', 'downloaded_at', 'ip_address']

