"""
CircleOptimizer 測試腳本
直接測試優化算法和 API 功能
"""
import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, r'C:\Users\06727\CODE\CoDevStudio')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from CircleOptimizer.models import Shape, CircleConfig, Circle
from CircleOptimizer.optimizer import optimize_3_circles, optimize_4_circles

def test_optimizer():
    """測試優化算法"""
    print("=" * 60)
    print("測試隧道斷面優化算法")
    print("=" * 60)
    
    # 測試數據：隧道斷面控制點
    test_points = [
        [20, 0], [20, 15], [15, 15], [15, 20],
        [-15, 20], [-15, 15], [-20, 15], [-20, 0]
    ]
    
    print("\n控制點座標:")
    for i, point in enumerate(test_points):
        print(f"  點 {i+1}: {point}")
    
    # 測試 3心圓優化
    print("\n" + "-" * 60)
    print("測試 3心圓優化...")
    print("-" * 60)
    result_3 = optimize_3_circles(test_points)
    
    if result_3['success']:
        print("✓ 優化成功!")
        print(f"  總面積: {result_3['total_area']:.4f}")
        for i, circle in enumerate(result_3['circles']):
            print(f"\n  圓 {i+1}:")
            print(f"    圓心: ({circle['center_x']:.2f}, {circle['center_y']:.2f})")
            print(f"    半徑: {circle['radius']:.2f}")
            print(f"    弧長: {circle['arc_length']:.2f}")
            print(f"    角度: {circle['start_angle']:.2f}° ~ {circle['end_angle']:.2f}°")
    else:
        print("✗ 優化失敗")
        print(f"  訊息: {result_3.get('message', '未知錯誤')}")
    
    # 測試 4心圓優化
    print("\n" + "-" * 60)
    print("測試 4心圓優化...")
    print("-" * 60)
    result_4 = optimize_4_circles(test_points)
    
    if result_4['success']:
        print("✓ 優化成功!")
        print(f"  總面積: {result_4['total_area']:.4f}")
        for i, circle in enumerate(result_4['circles']):
            print(f"\n  圓 {i+1}:")
            print(f"    圓心: ({circle['center_x']:.2f}, {circle['center_y']:.2f})")
            print(f"    半徑: {circle['radius']:.2f}")
            print(f"    弧長: {circle['arc_length']:.2f}")
            print(f"    角度: {circle['start_angle']:.2f}° ~ {circle['end_angle']:.2f}°")
    else:
        print("✗ 優化失敗")
        print(f"  訊息: {result_4.get('message', '未知錯誤')}")
    
    # 比較結果
    if result_3['success'] and result_4['success']:
        print("\n" + "=" * 60)
        print("比較結果")
        print("=" * 60)
        print(f"3心圓總面積: {result_3['total_area']:.4f}")
        print(f"4心圓總面積: {result_4['total_area']:.4f}")
        diff = result_3['total_area'] - result_4['total_area']
        print(f"差異: {diff:.4f} ({(diff/result_3['total_area']*100):.2f}%)")

def test_database():
    """測試資料庫模型"""
    print("\n" + "=" * 60)
    print("測試資料庫模型")
    print("=" * 60)
    
    # 創建測試圖形
    test_points = [
        [20, 0], [20, 15], [15, 15], [15, 20],
        [-15, 20], [-15, 15], [-20, 15], [-20, 0]
    ]
    
    shape = Shape.objects.create(
        name="隧道斷面測試 - 自動測試",
        points=test_points
    )
    print(f"\n✓ 創建圖形: {shape.name} (ID: {shape.id})")
    print(f"  控制點數量: {shape.points_count}")
    
    # 執行優化並保存
    result = optimize_3_circles(test_points)
    if result['success']:
        config = CircleConfig.objects.create(
            shape=shape,
            config_type='3_circle',
            total_area=result['total_area'],
            is_optimized=True
        )
        print(f"\n✓ 創建圓配置 (ID: {config.id})")
        
        for circle_data in result['circles']:
            circle = Circle.objects.create(
                config=config,
                circle_index=circle_data['circle_index'],
                center_x=circle_data['center_x'],
                center_y=circle_data['center_y'],
                radius=circle_data['radius'],
                arc_length=circle_data['arc_length'],
                start_angle=circle_data['start_angle'],
                end_angle=circle_data['end_angle']
            )
            print(f"  ✓ 創建圓 {circle.circle_index + 1}")
        
        print(f"\n✓ 配置包含 {config.circle_count} 個圓")
    
    # 清理測試數據
    shape.delete()
    print("\n✓ 清理測試數據完成")

if __name__ == '__main__':
    try:
        test_optimizer()
        test_database()
        print("\n" + "=" * 60)
        print("所有測試完成!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
