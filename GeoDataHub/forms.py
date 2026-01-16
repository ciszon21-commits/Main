"""
GeoDataHub Forms
=================
表單定義
"""

from django import forms
from .models import GeoCategory, GeoLocation, GeoDataSource, DataTag


class GeoLocationForm(forms.ModelForm):
    """地理位置表單 - 支援地圖標記"""
    
    address_search = forms.CharField(
        required=False,
        label='地址搜尋',
        widget=forms.TextInput(attrs={
            'class': 'pixel-input',
            'placeholder': '輸入地址搜尋...',
            'id': 'address-search'
        }),
        help_text='輸入地址後點擊搜尋按鈕，或直接在地圖上點選標記'
    )

    class Meta:
        model = GeoLocation
        fields = ['latitude', 'longitude', 'address', 'city', 'district', 'country', 
                  'geometry_type', 'geometry_data', 'is_manually_adjusted']
        widgets = {
            'latitude': forms.NumberInput(attrs={
                'class': 'pixel-input',
                'step': '0.00000001',
                'id': 'id_latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'pixel-input',
                'step': '0.00000001',
                'id': 'id_longitude'
            }),
            'address': forms.TextInput(attrs={
                'class': 'pixel-input',
                'id': 'id_address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'pixel-input'
            }),
            'district': forms.TextInput(attrs={
                'class': 'pixel-input'
            }),
            'country': forms.TextInput(attrs={
                'class': 'pixel-input'
            }),
            'geometry_type': forms.Select(attrs={
                'class': 'pixel-select'
            }),
            'geometry_data': forms.Textarea(attrs={
                'class': 'pixel-textarea',
                'rows': 3,
                'placeholder': 'GeoJSON 格式'
            }),
            'is_manually_adjusted': forms.CheckboxInput(attrs={
                'class': 'pixel-checkbox'
            }),
        }


class GeoDataSourceForm(forms.ModelForm):
    """資料來源表單"""
    
    # 新增標籤輸入
    new_tags = forms.CharField(
        required=False,
        label='新增標籤',
        widget=forms.TextInput(attrs={
            'class': 'pixel-input',
            'placeholder': '以逗號分隔多個標籤'
        }),
        help_text='輸入新標籤，以逗號分隔'
    )

    class Meta:
        model = GeoDataSource
        fields = ['title', 'description', 'source_type', 'category', 'tags',
                  'file', 'external_url', 'opensearch_index', 'opensearch_doc_id',
                  'metadata', 'thumbnail', 'is_visible', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'pixel-input',
                'placeholder': '資料標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'pixel-textarea',
                'rows': 4,
                'placeholder': '資料描述...'
            }),
            'source_type': forms.Select(attrs={
                'class': 'pixel-select',
                'id': 'id_source_type'
            }),
            'category': forms.Select(attrs={
                'class': 'pixel-select'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'pixel-select',
                'size': 5
            }),
            'file': forms.FileInput(attrs={
                'class': 'pixel-file-input'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'pixel-input',
                'placeholder': 'https://...'
            }),
            'opensearch_index': forms.TextInput(attrs={
                'class': 'pixel-input',
                'placeholder': 'index_name'
            }),
            'opensearch_doc_id': forms.TextInput(attrs={
                'class': 'pixel-input',
                'placeholder': 'document_id'
            }),
            'metadata': forms.Textarea(attrs={
                'class': 'pixel-textarea',
                'rows': 3,
                'placeholder': '{"key": "value"}'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'pixel-file-input'
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'pixel-checkbox'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'pixel-checkbox'
            }),
        }

    def clean_new_tags(self):
        """處理新標籤"""
        new_tags = self.cleaned_data.get('new_tags', '')
        if new_tags:
            tag_names = [t.strip() for t in new_tags.split(',') if t.strip()]
            return tag_names
        return []

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # 處理新標籤
            new_tag_names = self.cleaned_data.get('new_tags', [])
            for tag_name in new_tag_names:
                tag, created = DataTag.objects.get_or_create(name=tag_name)
                instance.tags.add(tag)
        
        return instance


class GeoCategoryForm(forms.ModelForm):
    """資料分類表單"""
    
    class Meta:
        model = GeoCategory
        fields = ['name', 'icon', 'color', 'description', 'opensearch_pattern', 
                  'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'pixel-input'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'pixel-input',
                'placeholder': '📍'
            }),
            'color': forms.TextInput(attrs={
                'class': 'pixel-input',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'pixel-textarea',
                'rows': 3
            }),
            'opensearch_pattern': forms.TextInput(attrs={
                'class': 'pixel-input',
                'placeholder': 'sinoproject*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'pixel-checkbox'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'pixel-input'
            }),
        }


class GeoSearchForm(forms.Form):
    """地理搜尋表單"""
    
    keyword = forms.CharField(
        required=False,
        label='關鍵字',
        widget=forms.TextInput(attrs={
            'class': 'pixel-input pixel-search-input',
            'placeholder': '🔍 輸入關鍵字...',
            'id': 'geo-search-keyword'
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=GeoCategory.objects.filter(is_active=True),
        label='分類',
        empty_label='全部分類',
        widget=forms.Select(attrs={
            'class': 'pixel-select',
            'id': 'geo-search-category'
        })
    )
    
    source_type = forms.ChoiceField(
        required=False,
        choices=[('', '全部類型')] + list(GeoDataSource.SourceType.choices),
        label='來源類型',
        widget=forms.Select(attrs={
            'class': 'pixel-select',
            'id': 'geo-search-source-type'
        })
    )
    
    # 隱藏欄位：地圖邊界
    bounds_north = forms.FloatField(required=False, widget=forms.HiddenInput())
    bounds_south = forms.FloatField(required=False, widget=forms.HiddenInput())
    bounds_east = forms.FloatField(required=False, widget=forms.HiddenInput())
    bounds_west = forms.FloatField(required=False, widget=forms.HiddenInput())
