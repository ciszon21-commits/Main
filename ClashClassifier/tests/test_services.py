from django.test import TestCase
from io import StringIO
from ClashClassifier.services import extract_system_code, clean_text, parse_html_to_records, records_to_csv_content

class ServiceTest(TestCase):
    def test_extract_system_code(self):
        """測試系統代碼提取"""
        self.assertEqual(extract_system_code("DN-D3-DR-00000-0A.rvt"), "DR")
        self.assertEqual(extract_system_code("DN-D3-SW-00000-0A.rvt"), "SW")
        self.assertEqual(extract_system_code("unknown_file.rvt"), "")
        
    def test_clean_text(self):
        """測試文字清理"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("<td>  Content  \n  Line2 </td>", "html.parser")
        cell = soup.find("td")
        self.assertEqual(clean_text(cell), "Content Line2")

    def test_parse_html_to_records(self):
        """測試 HTML 解析"""
        html_content = """
        <html>
        <body>
            <table class="mainTable">
                <tr class="contentRow">
                    <td>Img</td><td>Date</td><td>新</td><td>5.5</td>
                    <td>Grid</td><td>Level</td><td>Layer</td>
                    <td>Element Name: 123</td><td>Item1 ID</td><td>Item1 ID</td><td>Item1 File: F-DR-1.rvt</td>
                    <td>Pt</td><td>Layer</td><td>Category1</td><td>Other</td><td>Family1</td>
                    <td>Element Name: 456</td><td>Item2 ID</td><td>Item2 ID</td><td>Item2 File: F-SW-2.rvt</td>
                    <td>Pt</td><td>Layer</td><td>Category2</td><td>Other</td><td>Family2</td>
                    <td>Extra...</td>
                </tr>
            </table>
        </body>
        </html>
        """
        html_file = StringIO(html_content)
        records = parse_html_to_records(html_file)
        
        self.assertEqual(len(records), 1)
        record = records[0]
        
        self.assertEqual(record['distance'], 5.5)
        self.assertEqual(record['status'], 2) # 新 = 2
        self.assertEqual(record['item1_id'], "123")
        self.assertEqual(record['item1_system'], "DR")
        self.assertEqual(record['item1_type'], "Category1-Family1")
        self.assertEqual(record['item2_id'], "456")
        self.assertEqual(record['item2_system'], "SW")
        self.assertEqual(record['item2_type'], "Category2-Family2")

    def test_records_to_csv_content(self):
        """測試 CSV 生成"""
        records = [{
            "distance": 5.5,
            "item1_count": 1,
            "item1_system": "DR",
            "item1_type": "Type1",
            "item2_count": 1,
            "item2_system": "SW",
            "item2_type": "Type2",
            "status": 2,
        }]
        
        csv_content = records_to_csv_content(records)
        lines = csv_content.strip().split('\r\n')
        
        self.assertEqual(len(lines), 2) # Header + 1 row
        self.assertIn("衝突距離", lines[0])
        self.assertIn("5.5", lines[1])
