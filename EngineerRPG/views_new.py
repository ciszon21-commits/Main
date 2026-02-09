from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Prefetch
from django.core.paginator import Paginator
import random
import json

from .models import (
    CharacterClass, UserProfile, SkillNode, Course, UserSkill,
    Equipment, UserEquipment, Item, UserItem, Question, QuestionCategory, Trial, TrialRecord,
    PromotionRequest, EnhancementScroll, Achievement, UserAchievement,
    Team, TeamMembership, GuildPost, GuildComment
)


# ==================== Helper Functions ====================

def get_or_create_user_profile(user):
    """Get or create user profile"""
    try:
        return user.rpg_profile
    except UserProfile.DoesNotExist:
        # Create default profile
        default_class = CharacterClass.objects.first()
        if not default_class:
            raise Exception("No character class available")
        
        profile = UserProfile.objects.create(
            user=user,
            employee_id=f"EMP{user.id:04d}",
            character_class=default_class
        )
        return profile
