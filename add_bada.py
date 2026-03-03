import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import Restaurant, MenuItem

def run():
    restaurant_name = "八大便當粥品專賣"
    phone = "338-8215"
    address = "高雄市一心二路109號"

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
        ("宮保雞丁飯", 90, "chicken"),
        ("爌肉飯", 90, "pork"),
        ("麻油豬肉飯", 90, "pork"),
        ("排骨飯", 90, "pork"),
        ("鯖魚飯", 90, "fish"),
        ("黑胡椒豬肉飯", 90, "pork"),
        ("黑胡椒牛肉飯", 110, "beef"),
        ("蜜汁雞腿飯", 110, "chicken"),
        ("炸雞腿飯", 110, "chicken"),
        ("法式雞排飯", 110, "chicken"),
        ("豬腳飯", 110, "pork"),
        ("魚肚飯", 110, "fish"),
        ("肉燥飯", 40, "pork"),
        ("菜飯(5菜)", 70, "veg"),

        # 粥類
        ("魚肚粥", 100, "noodle"),
        ("蚵仔粥", 90, "noodle"),

        # 湯類
        ("魚丸湯", 35, "soup"),
        ("蛤仔湯", 40, "soup"),
        ("蚵仔湯", 80, "soup"),
        ("魚肚湯", 90, "soup"),

        # 單點主餐
        ("煎魚肚", 90, "single"),
        ("雞腿", 90, "single"),
        ("雞排", 90, "single"),
        ("排骨", 60, "single"),
        ("宮保", 60, "single"),
        ("麻油豬肉", 60, "single"),
        ("黑胡椒豬肉", 60, "single"),

        # 其他類
        ("魯蛋", 15, "side"),
        ("油豆腐", 10, "side"),
        ("燙青菜", 40, "side"),
        ("白飯", 10, "other"),
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
