
@login_required
def delete_question(request, question_id):
    """Delete a question"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:question_management')
        
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, '題目已刪除')
        
    return redirect('engineer_rpg:question_management')
