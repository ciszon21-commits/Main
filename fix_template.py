import os

filepath = 'EngineerRPG/templates/EngineerRPG/trial_exam.html'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

is_completed_idx = -1
elif_question_idx = -1
for i, l in enumerate(lines):
    if "{% if is_completed %}" in l:
        is_completed_idx = i
    if "{% elif question %}" in l and i > is_completed_idx:
        elif_question_idx = i
        break

chest_start = -1
chest_end = -1
for i in range(is_completed_idx, elif_question_idx):
    if "{% if chests %}" in lines[i]:
        chest_start = i
    if "{% endif %}" in lines[i] and "</style>" in lines[i-1]:
        chest_end = i

print(f"is_completed_idx: {is_completed_idx}")
print(f"elif_question_idx: {elif_question_idx}")
print(f"chest_start: {chest_start}")
print(f"chest_end: {chest_end}")

chest_logic = "".join(lines[chest_start:chest_end+1])

new_logic = """    <div class="completion-result text-center py-xl">
        {% if is_timeout %}
            <div class="result-icon mb-lg">
                <i class="fas fa-clock text-warning" style="font-size: 5rem;"></i>
            </div>
            <h2 class="text-warning mb-md">⏰ 時間到!</h2>
            <p class="text-lg text-stone mb-lg">時間已用盡,試煉失敗。</p>

        {% elif final_hp <= 0 %}
            <div class="result-icon mb-lg">
                <i class="fas fa-heart-broken text-danger" style="font-size: 5rem;"></i>
            </div>
            <h2 class="text-danger mb-md">💀 生命值歸零!</h2>
            <p class="text-lg text-stone mb-lg">很遺憾,您未能完成試煉。</p>

        {% elif is_passed %}
            {% if is_perfect %}
            <div class="result-icon mb-lg">
                <i class="fas fa-crown text-warning" style="font-size: 5rem;"></i>
            </div>
            <h2 class="text-warning mb-md">🎉 PERFECT CLEAR!</h2>
            <p class="text-lg text-stone mb-lg">完美通關！獲得雙倍經驗值與額外獎勵！</p>
            {% else %}
            <div class="result-icon mb-lg">
                <i class="fas fa-trophy text-primary" style="font-size: 5rem;"></i>
            </div>
            <h2 class="text-primary mb-md">🎉 挑戰成功!</h2>
            <p class="text-lg text-stone mb-lg">恭喜您完成了本次每日試煉!</p>
            {% endif %}

            <div class="row justify-content-center mb-4">
                <div class="col-md-8">
                    <div class="card bg-dark text-light border-secondary">
                        <div class="card-body">
                            <h5 class="card-title text-center mb-3">獲得獎勵</h5>
                            <div class="d-flex justify-content-around align-items-center">
                                <div class="text-center">
                                    <i class="fas fa-star text-warning fa-2x mb-2"></i>
                                    <p class="mb-0 text-muted">經驗值</p>
                                    <h4 class="text-warning">+{{ exp_reward }}</h4>
                                </div>
                                {% if ticket_reward > 0 %}
                                <div class="text-center">
                                    <i class="fas fa-ticket-alt text-info fa-2x mb-2"></i>
                                    <p class="mb-0 text-muted">強化券</p>
                                    <h4 class="text-info">+{{ ticket_reward }}</h4>
                                </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

""" + chest_logic + """
        {% else %}
            <div class="result-icon mb-lg">
                <i class="fas fa-times-circle text-danger" style="font-size: 5rem;"></i>
            </div>
            <h2 class="text-danger mb-md">❌ 挑戰失敗!</h2>
            <p class="text-lg text-stone mb-lg">正確率未達 60% (目前: {{ accuracy|floatformat:1 }}%)</p>
        {% endif %}

        <!-- 統計數據 -->
        <div class="stats-grid grid grid-cols-4 gap-md mb-xl max-w-3xl mx-auto">
            <div class="stat-card bg-black/30 p-md rounded">
                <div class="stat-value text-3xl font-bold text-primary">{{ correct_count }}</div>
                <div class="stat-label text-stone text-sm">答對題數</div>
            </div>
            <div class="stat-card bg-black/30 p-md rounded">
                <div class="stat-value text-3xl font-bold text-warning">{{ total_count }}</div>
                <div class="stat-label text-stone text-sm">總題數</div>
            </div>
            <div class="stat-card bg-black/30 p-md rounded">
                <div class="stat-value text-3xl font-bold text-secondary">{{ accuracy|floatformat:1 }}%</div>
                <div class="stat-label text-stone text-sm">正確率</div>
            </div>
            <div class="stat-card bg-black/30 p-md rounded">
                <div class="stat-value text-3xl font-bold {% if final_hp > 0 %}text-success{% else %}text-danger{% endif %}">
                    {{ final_hp }} / {{ initial_hp }}</div>
                <div class="stat-label text-stone text-sm">最終 HP</div>
            </div>
        </div>

        <!-- 返回按鈕 -->
        <a href="{% url 'engineer_rpg:daily_trial_list' %}" class="rpg-btn rpg-btn-primary btn-large mb-lg">
            <i class="fas fa-home"></i> 返回每日挑戰列表
        </a>
    </div>
"""

new_lines = lines[:is_completed_idx + 1] + [new_logic] + lines[elif_question_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Template fixed.")
