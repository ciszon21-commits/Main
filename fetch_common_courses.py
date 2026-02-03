
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import SkillNode

def get_common_required_courses():
    # Filter for ROOT type nodes (Common Required)
    nodes = SkillNode.objects.filter(node_type='ROOT')
    
    result = []
    for n in nodes:
        courses = n.courses.all()
        course_list = []
        for c in courses:
            course_list.append({
                'title': c.title,
                'description': c.description,
                'type': c.get_content_type_display(),
                'url': c.content_url
            })
            
        result.append({
            'skill_name': n.name,
            'description': n.description,
            'courses': course_list
        })
    
    return result

if __name__ == '__main__':
    data = get_common_required_courses()
    print(json.dumps(data, ensure_ascii=False, indent=2))
