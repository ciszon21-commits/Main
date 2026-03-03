import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import Restaurant, MenuItem

def run():
    restaurant_name = "外帶香中鴨"
    phone = "07-3347353"
    address = "高雄市前鎮區復興三路 139號"

    # 建立或取得餐廳
    restaurant, created = Restaurant.objects.get_or_create(
        name=restaurant_name,
        defaults={
            'phone': phone,
            'address': address,
        }
    )

    if not created:
        print(f"餐廳 {restaurant_name} 已存在，正在更新資料...")
        restaurant.phone = phone
        restaurant.address = address
        restaurant.save()
        # 清除舊菜單以便重新建立
        restaurant.menu_items.all().delete()
    else:
        print(f"建立新餐廳: {restaurant_name}")

    menu_data = [
        # 飯類
        ("鴨肉飯(小)", 45, "duck"),
        ("鴨肉飯(大)", 55, "duck"),
        ("鴨肉便當", 80, "duck"),
        ("鴨肉蛋炒飯", 80, "duck"),
        ("蝦仁蛋炒飯", 80, "other"),
        ("肉絲蛋炒飯", 80, "pork"),
        ("蝦仁肉絲蛋炒飯", 80, "pork"),
        ("牛肉蛋炒飯", 90, "beef"),
        ("蛋炒飯", 60, "other"),
        ("牛肉燴飯", 90, "beef"),
        ("豬肉燴飯", 80, "pork"),
        ("當歸鴨肉麵線湯", 80, "noodle"),
        ("鴨肉麵(湯)(乾)", 60, "noodle"),
        ("鴨肉冬粉(湯)(乾)", 60, "noodle"),

        # 青菜類
        ("空心菜", 40, "veg"),
        ("地瓜葉", 40, "veg"),
        ("大陸妹", 40, "veg"),

        # 薑絲湯類
        ("薑絲鴨肉湯", 70, "soup"),
        ("薑絲鴨心湯", 50, "soup"),
        ("薑絲下水湯", 40, "soup"),
        ("薑絲米血湯", 40, "soup"),
        ("蛋花湯", 30, "soup"),

        # 當歸湯類
        ("當歸鴨肉湯", 70, "soup"),
        ("當歸鴨心湯", 60, "soup"),
        ("當歸下水湯", 50, "soup"),
        ("當歸米血湯", 40, "soup"),
        ("當歸清湯", 20, "soup"),

        # 川燙類
        ("燙豆芽鴨心", 60, "side"),
        ("燙豆芽下水", 50, "side"),
        ("燙米血", 40, "side"),
        ("蔥花蛋", 50, "side"),

        # 切盤類
        ("鴨肉切盤1份", 70, "side"),

        # 其它
        ("加飯(麵)", 15, "other"),
    ]

    for name, price, category in menu_data:
        MenuItem.objects.create(
            restaurant=restaurant,
            name=name,
            price=price,
            category=category
        )
        print(f"新增品項: {name} (${price})")

    print("完成！")

if __name__ == '__main__':
    run()
