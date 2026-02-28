"""
技能樹自動佈局工具函式
提取自 views.py 中的 api_auto_layout_skill_tree，
可同時用於「預覽（不存檔）」與「真正儲存佈局」。
"""
from collections import deque

from django.db.models import Q
from EngineerRPG.models import SkillNode


def _transitive_reduction(all_parent_ids):
    """
    對整棵技能樹執行遞移簡化（Transitive Reduction）。

    all_parent_ids: dict[int, list[int]]
        key = 節點 id, value = 該節點的所有 parent id 列表

    回傳與 all_parent_ids 相同結構但移除冗餘邊的字典。
    例如 A→B→C 且 A→C，則移除 A→C (因為 A 已可透過 B 到達 C)。
    """
    # 建立「子節點 → 父節點集合」字典 (child_to_parents)
    child_to_parents = {nid: set(pids) for nid, pids in all_parent_ids.items()}

    # 建立「父節點 → 子節點集合」字典 (parent_to_children)
    parent_to_children = {}
    for nid in child_to_parents:
        parent_to_children.setdefault(nid, set())
    for nid, pids in child_to_parents.items():
        for pid in pids:
            parent_to_children.setdefault(pid, set()).add(nid)

    reduced = {}
    for node_id, direct_parents in child_to_parents.items():
        essential = set(direct_parents)
        for p in direct_parents:
            # 如果 p 可以透過其他 direct_parents 到達 node_id，
            # 則 p→node_id 這條邊是冗餘的。
            # 換言之：如果 p 是 node_id 的某個其他父節點的祖先，則冗餘。
            other_parents = direct_parents - {p}
            if _is_ancestor_of_any(p, other_parents, child_to_parents):
                essential.discard(p)
        reduced[node_id] = list(essential)

    return reduced


def _is_ancestor_of_any(candidate, targets, child_to_parents):
    """
    檢查 candidate 是否為 targets 中任一節點的祖先。
    使用 BFS 從每個 target 向上搜尋其祖先。
    """
    if not targets:
        return False
    for target in targets:
        visited = set()
        queue = deque([target])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for parent in child_to_parents.get(current, []):
                if parent == candidate:
                    return True
                queue.append(parent)
    return False


def calculate_layout_data(class_code):
    """
    計算指定職業的技能樹佈局座標。

    回傳格式：
    [
        {
            'id': int,
            'name': str,
            'node_type': str,       # ROOT / CORE / ADVANCED
            'position_x': int,
            'position_y': int,
            'parent_ids': [int, ...],
            'exp_reward': int,
        },
        ...
    ]
    """
    skills = list(
        SkillNode.objects.filter(
            Q(node_type='ROOT') | Q(character_class__code=class_code)
        ).prefetch_related('parent_skills')
    )

    if not skills:
        return []

    # ---------- 第一步：計算每個節點的「層級」 (X軸) ----------
    levels = {s.id: 0 for s in skills}

    # 1. 共同必修 (ROOT) 節點獨立分層 (處理內部依賴)
    root_skills = [s for s in skills if s.node_type == 'ROOT']
    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1
        for s in root_skills:
            current_level = levels[s.id]
            max_p_lvl = -1
            for p in s.parent_skills.all():
                if p.id in levels and any(rs.id == p.id for rs in root_skills):
                    max_p_lvl = max(max_p_lvl, levels[p.id])
            if max_p_lvl >= current_level:
                levels[s.id] = max_p_lvl + 1
                changed = True
    
    max_root_lvl = max([levels[s.id] for s in root_skills] or [-1])
    base_for_others = max_root_lvl + 1 if max_root_lvl >= 0 else 0

    # 2. 職業核心 (CORE) 與 進階選修 (ADVANCED) 節點合併分層 (兩種類型可併行)
    other_skills = [s for s in skills if s.node_type in ['CORE', 'ADVANCED']]
    for s in other_skills:
        levels[s.id] = base_for_others

    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1
        for s in other_skills:
            current_level = levels[s.id]
            max_p_lvl = -1
            for p in s.parent_skills.all():
                if p.id in levels:
                    max_p_lvl = max(max_p_lvl, levels[p.id])
            if max_p_lvl >= current_level:
                levels[s.id] = max_p_lvl + 1
                changed = True

    # ---------- 第二步：依層級分組 ----------
    level_groups = {}
    for s in skills:
        lvl = levels[s.id]
        level_groups.setdefault(lvl, []).append(s)

    # ---------- 第三步：計算 X / Y 座標 ----------
    node_y_pos = {}
    result = []

    for lvl in sorted(level_groups.keys()):
        nodes = level_groups[lvl]
        x_pos = lvl * 250 + 50

        def get_parent_avg_y(node):
            """計算父節點的平均 Y 座標，若無則預設為中央 500"""
            assigned_parents = [p for p in node.parent_skills.all() if p.id in node_y_pos]
            if not assigned_parents:
                return 500
            return sum(node_y_pos[p.id] for p in assigned_parents) / len(assigned_parents)

        # Y 軸排序邏輯：
        # 1. ROOT/CORE (Main) 傾向居中
        # 2. ADVANCED (Extreme) 根據父節點位置傾向往兩端 (500為界) 偏移
        scored_nodes = []
        for n in nodes:
            avg_y = get_parent_avg_y(n)
            bias = 0
            if n.node_type == 'ADVANCED':
                # 進階選修賦予極大偏權值，確保其排在 Main 組的上方或下方
                bias = -100000 if avg_y < 500 else 100000
            scored_nodes.append((bias + avg_y, n))
        
        # 依「偏移權重 + 理想位置」排序
        scored_nodes.sort(key=lambda x: (x[0], x[1].name))
        sorted_nodes = [x[1] for x in scored_nodes]

        # 座標分配：以 ROOT/CORE 的中心點對齊 Y=500 進行平移
        main_indices = [i for i, n in enumerate(sorted_nodes) if n.node_type in ['ROOT', 'CORE']]
        if main_indices:
            center_idx = (min(main_indices) + max(main_indices)) / 2
        else:
            center_idx = (len(sorted_nodes) - 1) / 2 if sorted_nodes else 0
        
        for i, node in enumerate(sorted_nodes):
            # 計算初步 Y (間距 150)
            y_pos = 500 + (i - center_idx) * 150
            
            # 貼齊 50px 網格並確保不低於 50
            y_pos = max(50, round(y_pos / 50) * 50)
            
            node_y_pos[node.id] = y_pos

            result.append({
                'id': node.id,
                'name': node.name,
                'node_type': node.node_type,
                'position_x': x_pos,
                'position_y': y_pos,
                'parent_ids': [p.id for p in node.parent_skills.all()],
                'exp_reward': node.exp_reward,
            })

    # ---------- 第四步：遞移簡化（Transitive Reduction）----------
    # 移除冗餘的連接線 (例如 A→B→C 時，移除多餘的 A→C)
    all_parent_ids = {item['id']: item['parent_ids'] for item in result}
    reduced = _transitive_reduction(all_parent_ids)
    for item in result:
        item['parent_ids'] = reduced.get(item['id'], item['parent_ids'])

    return result


def apply_layout_to_db(class_code):
    """
    計算佈局後寫入資料庫（原有的自動佈局功能）。
    回傳處理的節點數量。
    """
    layout_data = calculate_layout_data(class_code)

    # 批量更新
    skill_map = {item['id']: item for item in layout_data}
    skills = SkillNode.objects.filter(id__in=skill_map.keys())

    for skill in skills:
        data = skill_map[skill.id]
        skill.position_x = data['position_x']
        skill.position_y = data['position_y']
        skill.save(update_fields=['position_x', 'position_y'])

    return len(layout_data)
