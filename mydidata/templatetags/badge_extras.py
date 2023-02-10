from django import template
register = template.Library()
from django.urls import reverse
from ..models import Profile

@register.simple_tag
def get_badge_img(badge):
    if(badge == Profile.INTEREST_IRON):
        return "/static/images/badges/iron_badge.png"
    if(badge == Profile.INTEREST_BRONZE):
        return "/static/images/badges/bronze_badge.png"
    if(badge == Profile.INTEREST_SILVER):
        return "/static/images/badges/silver_badge.png"
    if(badge == Profile.INTEREST_GOLD):
        return "/static/images/badges/gold_badge.png"
    if(badge == Profile.PARTICIPATION_IRON):
        return "/static/images/badges/iron_badge.png"
    if(badge == Profile.PARTICIPATION_BRONZE):
        return "/static/images/badges/bronze_badge.png"
    if(badge == Profile.PARTICIPATION_SILVER):
        return "/static/images/badges/silver_badge.png"
    if(badge == Profile.PARTICIPATION_GOLD):
        return "/static/images/badges/gold_badge.png"    
    if(badge == Profile.COLAB_IRON):
        return "/static/images/badges/iron_badge.png"
    if(badge == Profile.COLAB_BRONZE):
        return "/static/images/badges/bronze_badge.png"
    if(badge == Profile.COLAB_SILVER):
        return "/static/images/badges/silver_badge.png"
    if(badge == Profile.COLAB_GOLD):
        return "/static/images/badges/gold_badge.png"
    if(badge == Profile.CREATIVE_IRON):
        return "/static/images/badges/iron_badge.png"
    if(badge == Profile.CREATIVE_BRONZE):
        return "/static/images/badges/bronze_badge.png"
    if(badge == Profile.CREATIVE_SILVER):
        return "/static/images/badges/silver_badge.png"
    if(badge == Profile.CREATIVE_GOLD):
        return "/static/images/badges/gold_badge.png"
    return ""
@register.simple_tag
def get_badge_name(badge):
    return Profile.get_badge_name(badge)
    
    
    
    
    
    
    
    
	
	