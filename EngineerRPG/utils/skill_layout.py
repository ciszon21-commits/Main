"""
技能樹自動佈局工具函式
提取自 views.py 中的 api_auto_layout_skill_tree，
可同時用於「預覽（不存檔）」與「真正儲存佈局」。
"""
from collections import deque

from django.db.models import Q
from EngineerRPG.models import SkillNode


def transitive_reduction(all_parent_ids):
    """
    對整棵技能樹執行遞移簡化（Transitive Reduction）。
    原則 3 & 5：
    1. 保留組內依賴：若 A→B 且 {A,B} 皆為 C 的父節點，保留 A→C 以成群組。
    2. 跨層級簡化：若 C 的父節點集合為 {A,B}，且 D 的父節點集合包含 {A,B,C}，則 D 僅需連接至 C。
    """
    child_to_parents = {nid: set(pids) for nid, pids in all_parent_ids.items()}
    reduced = {}

    for node_id, parents in child_to_parents.items():
        essential = set(parents)
        for p in list(parents):
            # 原則 5: 如果 p 是我的父節點，且 p 的所有父節點也是我的直系父節點，
            # 則我與 p 的父節點間的連線是冗餘的 (因為 p 已經概括了它們)。
            p_parents = child_to_parents.get(p, set())
            if p_parents and p_parents.issubset(parents):
                for pp in p_parents:
                    essential.discard(pp)
        
        reduced[node_id] = list(essential)

    return reduced


def is_ancestor_of_any(candidate, targets, child_to_parents):
    """
    檢查 candidate 是否為 targets 中任一節點的祖先。
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
    """
    skills = list(
        SkillNode.objects.filter(
            Q(node_type='ROOT') | Q(character_class__code=class_code)
        ).prefetch_related('parent_skills')
    )

    if not skills:
        return []

    # ---------- 第一步：計算 X 軸層級 ----------
    levels = {s.id: 0 for s in skills}
    node_map = {s.id: s for s in skills}
    
    # 1. 共同必修 (ROOT)
    root_skills = [s for s in skills if s.node_type == 'ROOT']
    changed = True
    while changed:
        changed = False
        for s in root_skills:
            max_p_lvl = -1
            for p in s.parent_skills.all():
                if p.id in levels and node_map[p.id].node_type == 'ROOT':
                    max_p_lvl = max(max_p_lvl, levels[p.id])
            if max_p_lvl >= levels[s.id]:
                levels[s.id] = max_p_lvl + 1
                changed = True
    
    max_root_lvl = max([levels[s.id] for s in root_skills] or [-1])
    base_for_others = max_root_lvl + 1 if max_root_lvl >= 0 else 0

    # 2. 職業核心 (CORE) 與 進階選修 (ADVANCED)
    other_skills = [s for s in skills if s.node_type in ['CORE', 'ADVANCED']]
    for s in other_skills:
        levels[s.id] = base_for_others

    changed = True
    while changed:
        changed = False
        for s in other_skills:
            max_p_lvl = -1
            for p in s.parent_skills.all():
                if p.id in levels:
                    max_p_lvl = max(max_p_lvl, levels[p.id])
            if max_p_lvl >= levels[s.id]:
                levels[s.id] = max_p_lvl + 1
                changed = True

    # 3. 方案 B：群組對齊 (Group Alignment)
    # 識別共享子節點且類型相似的父節點，強制對齊其 Level 以供視覺群組顯示
    potential_groups_for_alignment = []
    for s in skills:
        pids = [p.id for p in s.parent_skills.all() if p.id in levels]
        if len(pids) >= 2:
            # 原則 1: 僅分 ROOT 與 OTHER
            root_pids = [pid for pid in pids if node_map[pid].node_type == 'ROOT']
            other_pids = [pid for pid in pids if node_map[pid].node_type != 'ROOT']
            if len(root_pids) >= 2: potential_groups_for_alignment.append(set(root_pids))
            if len(other_pids) >= 2: potential_groups_for_alignment.append(set(other_pids))

    if potential_groups_for_alignment:
        alignment_changed = True
        while alignment_changed:
            alignment_changed = False
            # a. 拉齊群組內的 Level 到最大值
            for group in potential_groups_for_alignment:
                max_group_lvl = max(levels[pid] for pid in group)
                for pid in group:
                    if levels[pid] < max_group_lvl:
                        # 檢查：不能讓父節點推移到與子節點相同或更右邊的位置
                        # 找出這個父節點的所有直接子節點
                        node_children = [s.id for s in skills if node_map[pid] in s.parent_skills.all()]
                        min_child_lvl = min([levels[cid] for cid in node_children] or [1000])
                        
                        # 最高原則：X 座標禁止相同。父節點必須 < 子節點
                        if max_group_lvl < min_child_lvl:
                            levels[pid] = max_group_lvl
                            alignment_changed = True
            
            # b. 若有變動，必須重新傳遞 (Propagate) 影響至所有子節點
            if alignment_changed:
                propagation_changed = True
                while propagation_changed:
                    propagation_changed = False
                    for s in skills:
                        max_p_lvl = -1
                        for p in s.parent_skills.all():
                            if p.id in levels:
                                max_p_lvl = max(max_p_lvl, levels[p.id])
                        if max_p_lvl >= levels[s.id]:
                            # 嚴格落實：子節點 X 必須大於父節點
                            levels[s.id] = max_p_lvl + 1
                            propagation_changed = True

    # ---------- 第二步：計算路徑權重 (為達成中軸線原則) ----------
    level_groups_data = {}
    for s in skills:
        lvl = levels[s.id]
        level_groups_data.setdefault(lvl, []).append(s)

    # 1. 計算每個節點往後的最長深度 (Subtree Depth)
    subtree_depth = {s.id: 0 for s in skills}
    # 從最後一層往前算
    for lvl in sorted(level_groups_data.keys(), reverse=True):
        for s in level_groups_data[lvl]:
            # 獲取資料庫中的所有子節點
            children = [child for child in skills if s in child.parent_skills.all()]
            if children:
                subtree_depth[s.id] = 1 + max(subtree_depth[c.id] for c in children)
    
    # 2. 計算節點總權重 (Priority = X層級 + 子樹深度)
    node_priority = {s.id: levels[s.id] + subtree_depth[s.id] for s in skills}

    # 3. 識別視覺群組 (幫助 Y 軸排序時靠攏)
    node_potential_group_id = {s.id: None for s in skills}
    group_id_counter = 0
    for s in skills:
        pids = [p.id for p in s.parent_skills.all() if p.id in levels]
        if len(pids) >= 2:
            group_id_counter += 1
            for pid in pids:
                # 簡單處理：一個節點只屬於一個最具代表性的群組 (以此子節點為首)
                if node_potential_group_id[pid] is None:
                    node_potential_group_id[pid] = group_id_counter

    # ---------- 第三步：依層級分組並分配 Y 座標 ----------
    node_y_pos = {}
    result = []

    for lvl in sorted(level_groups_data.keys()):
        nodes = level_groups_data[lvl]
        x_pos = lvl * 250 + 50

        # 計算理想 Y (基於父節點)
        def get_ideal_y(node):
            assigned_parents = [p for p in node.parent_skills.all() if p.id in node_y_pos]
            if not assigned_parents: return 200 # 預設從上方開始
            
            # 優先跟隨權重最高的父節點 (主幹拉力)
            main_parent = max(assigned_parents, key=lambda p: node_priority[p.id])
            return node_y_pos[main_parent.id]

        # 排序：權重越高 (主幹) 越靠前
        scored_nodes = []
        for n in nodes:
            ideal = get_ideal_y(n)
            prio = node_priority[n.id]
            group_id = node_potential_group_id[n.id] or 999999
            # 增加 group_id 權重，確保同組節點在排序中相鄰
            scored_nodes.append({'node': n, 'prio': prio, 'ideal': ideal, 'group_id': group_id})
        
        # 排序權重：
        # 1. 權重 (Priority) 決定由上而下的層次 (主幹最上)
        # 2. 群組 ID 確保同組的節點被排在一起
        # 3. 理想 Y 座標
        scored_nodes.sort(key=lambda x: (-x['prio'], x['group_id'], x['ideal']))
        sorted_nodes = [x['node'] for x in scored_nodes]

        # 座標分配 (由上而下分配)
        for i, node in enumerate(sorted_nodes):
            # 基推 Y 值：從 200 開始，間距 150
            y_pos = 200 + i * 150
            
            # 水平拉直邏輯：如果你是父節點權重最高的延續分支
            assigned_parents = [p for p in node.parent_skills.all() if p.id in node_y_pos]
            if assigned_parents:
                best_parent = max(assigned_parents, key=lambda p: node_priority[p.id])
                if node_priority[node.id] >= 5 and node_priority[node.id] == node_priority[best_parent.id] - 1:
                     y_pos = node_y_pos[best_parent.id]

            y_pos = max(50, round(y_pos / 50) * 50)
            
            # 防止同層 Y 座標完全重疊 (除非是強制對齊的群組)
            while any(y_pos == node_y_pos[other.id] for other in nodes if other.id in node_y_pos):
                y_pos += 150
                
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

    # ---------- 第四步：水平衝突避讓 (避免連線穿過節點) ----------
    def resolve_horizontal_collisions():
        changed = False
        # 構建線條清單：每一條連線的「水平進入段」
        # 進入段範圍：[x_parent + 125, x_child] 且 Y = y_child
        lines = []
        for s in skills:
            if s.id not in node_y_pos: continue
            child_lvl = levels[s.id]
            child_x = child_lvl * 250 + 50
            child_y = node_y_pos[s.id]
            
            for p in s.parent_skills.all():
                if p.id not in levels or p.id not in node_y_pos: continue
                parent_lvl = levels[p.id]
                parent_x = parent_lvl * 250 + 50
                
                # 如果跳過了一層以上，才有穿越風險
                if child_lvl > parent_lvl + 1:
                    # 連線轉折點 X: parent_x + 125
                    lane_x = parent_x + 125
                    lines.append({
                        'x_start': lane_x,
                        'x_end': child_x,
                        'y': child_y,
                        'child_id': s.id
                    })

        # 檢查每個節點是否撞到這些線
        for i, r in enumerate(result):
            sid = r['id']
            nx = r['position_x']
            ny = r['position_y']
            
            for line in lines:
                # 衝突判定：Y 相同，且節點 X 落在連線的水平進入段內
                # (注意：排除連線的終點節點本身)
                if ny == line['y'] and line['x_start'] < nx < line['x_end']:
                    # 發生衝突！將節點向下推移
                    node_y_pos[sid] += 150
                    result[i]['position_y'] = node_y_pos[sid]
                    changed = True
                    break # 一次推移一個位置
        return changed

    # 迭代直到沒有任何衝突
    max_iterations = 20
    for _ in range(max_iterations):
        if not resolve_horizontal_collisions():
            break

    # ---------- 第五步：遞移簡化 (原則 3 & 5) ----------
    all_parent_ids = {item['id']: item['parent_ids'] for item in result}
    reduced = transitive_reduction(all_parent_ids)
    for item in result:
        item['parent_ids'] = reduced.get(item['id'], item['parent_ids'])

    return result

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
