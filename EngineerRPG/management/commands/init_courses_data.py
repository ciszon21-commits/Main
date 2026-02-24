"""
課程初始化資料
此檔案由 export_courses command 自動生成
包含課程資料及其與技能節點、題目的關聯
"""

# 課程資料
COURSES = [
    {
        "title": "新進監造工程師訓練",
        "description": "新人必修的基礎訓練課程，涵蓋行政作業、法規與安全。",
        "content_type": "PDF",
        "content_url": "https://example.com/novice-training",
        "duration_minutes": 180,
        "passing_score": 80,
        "exam_time_limit": 20,
        "skill_node_names": [
            "監造行政作業基礎",
            "工程法規概論",
            "工地安全衛生基礎",
            "監造權責與倫理"
        ],
        "question_category_names": [
            "品質管理"
        ],
        "question_count": 3
    },
    {
        "title": "PMIS課程(初中高階)_常時課程",
        "description": "課程內容分為初、中、高階三種類型課程\r\nPMIS初階訓練，主題有:1.數位轉型之路&考評機制數位轉型之路&考評機制、2.PMIS概論、3.PMIS一開始要做的事，\r\n課程內容:給予學員正確觀念，簡介PMIS的基本架構、帳號的設定與登入、教學資源(手冊、影片)，設定標案基本資料、公文系統背景設定及重要計畫書管控時程、契約與ISO規定必做事項。\r\nPMIS中階訓練，主題有:1.PMIS對於工作實務必作項目(一)、2.PMIS對於工作實務必作項目(二)、3.PMIS對於工作實務必作項目(三)。\r\n課程內容:公文管理基本登記與串聯操作、文件提審-文件審查管控、符合ISO相關規定，工地查驗-新增一筆查驗資料、檢試驗管制、資料設定(構造物等)、監造報表-統計圖表、監造報表匯入、文檔協同-文件上傳專區、中興職安衛專區、K槽/P槽應用與管理、文件庫總覽、會議管理、工作管理、照片管理等。\r\nPMIS高階訓練，主題有:1.PMIS各功能延伸使用(一)。2. PMIS各功能延伸使用(二)。3. PMIS各功能延伸使用(三)。\r\n課程內容:電子化查驗系統-施工抽查、安衛抽查、材料抽查、範本資料庫設定與操作、線上簽核系統-公文雲端簽辦之操作、BIM模組、LINE-BIM簡介、LINE等資源之串接、其他(履歷管理平台、契約審查資料庫、廠商資料庫、內稽系統、結案系統簡介)",
        "content_type": "LINK",
        "content_url": "https://fms.sinotech.com.tw/course/syllabus?courseId=339",
        "duration_minutes": 30,
        "passing_score": 60,
        "exam_time_limit": 20,
        "skill_node_names": [
            "PMIS初階",
            "PMIS中階",
            "PMIS高階"
        ],
        "question_category_names": [
            "品質管理",
            "施工管理",
            "工務行政"
        ],
        "question_count": 40
    },
    {
        "title": "監造計畫編撰重點暨執行實務上集",
        "description": "監造計畫撰寫與執行的實務課程，特別針對第一章至第五章的內容進行詳細說明。",
        "content_type": "LINK",
        "content_url": "https://fms.sinotech.com.tw/media/3982",
        "duration_minutes": 30,
        "passing_score": 80,
        "exam_time_limit": 20,
        "skill_node_names": [],
        "question_category_names": [
            "品質管理"
        ],
        "question_count": 4
    },
    {
        "title": "監造計畫編撰重點暨執行實務下集",
        "description": "監造計畫撰寫與執行的實務課程，特別針對第六章至第九章的內容進行詳細說明。",
        "content_type": "LINK",
        "content_url": "https://fms.sinotech.com.tw/media/4461",
        "duration_minutes": 30,
        "passing_score": 80,
        "exam_time_limit": 20,
        "skill_node_names": [],
        "question_category_names": [
            "品質管理"
        ],
        "question_count": 3
    },
    {
        "title": "安全衛生監督查核計畫撰寫平台",
        "description": "旨在提高公共工程職業安全與衛生的管理效率。該平臺基於公司PMIS系統，整合了相關檔案範本和流程，幫助工程人員快速、準確地完成計劃書的編寫。透過PDCA模式，此平臺自動化了許多步驟，減少重複工作並提升版本控制的透明度。",
        "content_type": "LINK",
        "content_url": "https://fms.sinotech.com.tw/media/4077",
        "duration_minutes": 30,
        "passing_score": 80,
        "exam_time_limit": 20,
        "skill_node_names": [],
        "question_category_names": [
            "職安衛"
        ],
        "question_count": 10
    },
    {
        "title": "工程技術論壇-從台鐵太魯閣號火車事故探討台灣軌道工程安全問題",
        "description": "臺灣鐵路泰魯閣號事故引起了對軌道工程安全問題的關注。專家指出，事故的根本原因在於施工過程中的疏忽和管理不善，包括未遵守安全規範、缺乏有效的風險評估與控制措施等。報告強調需要從設計階段就開始考慮施工風險，並提出了一系列改進措施，如加強現場安全管理、完善隧道邊坡防護設施、建立更完善的施工風險資料庫等。此外，還建議通過培訓和E-learning平臺提高員工的風險意識和技術水平，以確保未來類似事故不再發生。",
        "content_type": "LINK",
        "content_url": "https://fms.sinotech.com.tw/media/573",
        "duration_minutes": 30,
        "passing_score": 80,
        "exam_time_limit": 20,
        "skill_node_names": [],
        "question_category_names": [
            "職安衛"
        ],
        "question_count": 10
    }
]
