


## 代辦事項


### 背景環境設置
- [ ] 1. 製作可以簡單切換「本機開發」和「實際上線」模式的方法
- [ ] 2. 測試不同環境下不同功能是否能正常運作
  - [ ] 2.0 撰寫單元測試？
  - [ ] 2.1 Login
    - [ ] 2.1.1 本機開發 - SingleAuth 登入
    - [ ] 2.1.2 正式上線 - BimToken 登入
  - [ ] 2.2 SinoArchive
    - [ ] 2.2.1 本機開發 - 功能要失效，但不可以出錯(500)
    - [ ] 2.2.2 正式上線 - 使用 PMISReader 正式使用


### 開發環境需要
- [-] a. 需要支援 public service
- [O] a.1 get_user_json
- [O] b. 透過 single auth 註冊過後，也要可以新增 UserProfile
    - 更新的工作轉移到 Backend 內執行

### 正式環境需要
- [ ] A. 本專案藥可以兼容 SinoBimAuth
- [ ] A.1. SinoBimAuth 要可以避免在測試環境下讀取 (阻擋到登入)
- [O] B. 把 SinoArchive 改寫成 PMISReader 的方式
- [O] C. StudioBase 提供 public service 的方法





## 正式環境設置
```python
# local_settings.py


SINO_AUTH_SERVICE_TOKEN = '{PUBLIC_SAS_TOKEN}'
SINO_AUTH_SERVICE_DOMAIN = 'https://50-129.sinotech.com.tw:1127'
SINO_AUTH_SERVICE_APP_PATH = 'sas'


STAGE_MIDDLEWARES = [
    "CoDevStudio.middleware.user_auth.UserAuthMiddleware",  # django auth 之後
]


STAGE_READ_DB_LABELS = [
    'BimAuth',
    'CommonUse',
]
STAGE_WRITE_DB_LABELS = [
    'BimAuth',
]
STAGE_MIGRATE_DB_LABELS = []

```

