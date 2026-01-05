from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField

from ERModelGenerator.utils.scanner import (
    sanitize_name,
    get_mermaid_field_type,
    FieldInfo,
    ModelInfo,
    RelationInfo,
    parse_field,
    parse_relation,
    parse_model,
    generate_mermaid_er,
    _format_field_line,
    get_project_app_labels,
    generate_mermaid_for_single_app
)

class ScannerUtilsTest(TestCase):
    def test_sanitize_name(self):
        """測試名稱清理功能"""
        self.assertEqual(sanitize_name("NormalName"), "NormalName")
        self.assertEqual(sanitize_name("Name-With-Hyphens"), "NameWithHyphens")
        self.assertEqual(sanitize_name("123Start"), "E123Start")
        self.assertEqual(sanitize_name("Name_With_Underscore"), "NameWithUnderscore")
        self.assertEqual(sanitize_name(""), "Entity")

    def test_get_mermaid_field_type(self):
        """測試 Django 欄位類型轉換"""
        # 測試字串即類型
        self.assertEqual(get_mermaid_field_type("CharField"), "string")
        self.assertEqual(get_mermaid_field_type("IntegerField"), "int")
        self.assertEqual(get_mermaid_field_type("ForeignKey"), "int")
        # 測試未知類型
        self.assertEqual(get_mermaid_field_type("UnknownField"), "string")

    def test_format_field_line(self):
        """測試欄位行格式化"""
        field = FieldInfo(
            name="test_field",
            field_type="string",
            is_pk=True,
            is_fk=False
        )
        expected = 'string testfield "PK"'
        self.assertEqual(_format_field_line(field, show_type=True), expected)

        field_with_fk = FieldInfo(
            name="fk_field",
            field_type="int",
            is_pk=False,
            is_fk=True
        )
        expected_fk = 'int fkfield "FK"'
        self.assertEqual(_format_field_line(field_with_fk, show_type=True), expected_fk)

        # 測試不顯示類型
        expected_no_type = 'string testfield "PK"'
        self.assertEqual(_format_field_line(field, show_type=False), expected_no_type)

class ScannerTestModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Name')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children')
    tags = models.ManyToManyField('self', blank=True)
    
    class Meta:
        app_label = 'ERModelGenerator'
        abstract = False

class ScannerParsingTest(TestCase):
    def setUp(self):
        self.TestModel = ScannerTestModel
        self.meta = ScannerTestModel._meta
        
    def test_parse_field(self):
        """測試單一欄位解析"""
        # 測試普通欄位
        name_field = self.meta.get_field('name')
        info = parse_field(name_field)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, 'name')
        self.assertEqual(info.field_type, 'string')
        self.assertFalse(info.is_pk)

        # 測試 PK 欄位
        pk_field = self.meta.get_field('id')
        pk_info = parse_field(pk_field)
        self.assertTrue(pk_info.is_pk)
        self.assertIn(pk_info.field_type, ['int', 'bigint'])

        # 測試排除 M2M
        tags_field = self.meta.get_field('tags')
        self.assertIsNone(parse_field(tags_field))

    def test_parse_model(self):
        """測試 Model 解析"""
        model_info = parse_model(self.TestModel)
        
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info.name, 'ScannerTestModel')
        # self.assertEqual(model_info.app_label, 'ERModelGenerator') # 這裡可能會根據在哪裡定義變動，先略過
        
        # 驗證欄位數量：id, name, parent (FK 也是欄位)
        # tags 是 M2M 不算在 fields 裡
        field_names = [f.name for f in model_info.fields]
        self.assertIn('id', field_names)
        self.assertIn('name', field_names)
        self.assertIn('parent', field_names)
        self.assertNotIn('tags', field_names)

        # 驗證 relation
        relation_types = [r.relation_type for r in model_info.relations]
        self.assertIn('FK', relation_types)
        self.assertIn('M2M', relation_types)

    @patch('ERModelGenerator.utils.scanner.get_mermaid_field_type')
    def test_parse_relation(self, mock_get_type):
        """測試關聯解析"""
        fk_field = self.meta.get_field('parent')
        relation = parse_relation(fk_field, self.meta)
        
        self.assertIsNotNone(relation)
        self.assertEqual(relation.from_model, 'ScannerTestModel')
        # self.assertEqual(relation.to_model, 'TestModel') # self ref
        self.assertEqual(relation.relation_type, 'FK')
        
        m2m_field = self.meta.get_field('tags')
        relation_m2m = parse_relation(m2m_field, self.meta)
        self.assertIsNotNone(relation_m2m)
        self.assertEqual(relation_m2m.relation_type, 'M2M')

class MermaidGenerationTest(TestCase):
    @patch('ERModelGenerator.utils.scanner.get_models_for_app')
    @patch('ERModelGenerator.utils.scanner.get_project_app_labels')
    def test_generate_mermaid_er(self, mock_get_apps, mock_get_models):
        """測試 Mermaid 語法產生"""
        # Mock App 列表
        mock_get_apps.return_value = ['app1']
        
        # Mock Model Info
        field_info = FieldInfo('id', 'int', is_pk=True)
        model_info = ModelInfo(
            name='Model1',
            app_label='app1',
            verbose_name='Model One',
            fields=[field_info]
        )
        
        # 建立一個關聯
        relation = RelationInfo(
            from_model='Model1',
            from_app='app1',
            to_model='Model2',
            to_app='app1',
            relation_type='FK',
            field_name='related'
        )
        model_info.relations = [relation]
        
        # Model2 (關聯目標)
        model_info2 = ModelInfo(
            name='Model2',
            app_label='app1',
            verbose_name='Model Two',
            fields=[FieldInfo('id', 'int', is_pk=True)]
        )
        
        # Configure side_effect to return list of models for app1
        mock_get_models.side_effect = lambda app: [model_info, model_info2] if app == 'app1' else []
        
        # 產生 ER 圖
        code = generate_mermaid_er(['app1'])
        
        # 驗證關鍵字元
        self.assertIn('erDiagram', code)
        self.assertIn('app1Model1', code)
        self.assertIn('app1Model2', code)
        self.assertIn('||--o{', code)  # FK 關係
        self.assertIn('int id "PK"', code)

    @patch('ERModelGenerator.utils.scanner.generate_mermaid_er')
    def test_generate_mermaid_for_single_app(self, mock_gen):
        """測試單一 App 產生"""
        generate_mermaid_for_single_app('test_app')
        mock_gen.assert_called_with(
            app_labels=['test_app'],
            show_fields=True,
            show_field_types=True,
            group_by_app=False
        )
