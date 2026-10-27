"""
UK Food Store Rota Optimization Engine - Architecture V4 (Universal Reference)
Open-source reference and default configurations for UK Food Stores, Quick Service Restaurants (QSR),
and Hospitality Venues.
"""

from ortools.sat.python import cp_model
from typing import List, Dict, Any, Optional
import copy
import random

# ==============================================================================
# DEFAULT GLOBAL BOUNDARIES & RULES
# ==============================================================================

DEFAULT_GLOBAL_RULES = {
    "mandatory_days_off_per_week": 2,     # Max 5 days worked per week
    "min_shift_hours_for_break": 6.0,     # Shifts >= 6h get unpaid break
    "unpaid_break_duration_hours": 0.5,   # 30 mins unpaid break
    "min_rest_hours_between_shifts": 11.0,# UK Working Time Regulations
    "store_hours": {
        "Mon": {"open": "07:00", "close": "22:45", "food_start": "11:00", "food_end": "22:00", "order_day": True, "order_finish": "14:00"},
        "Tue": {"open": "09:00", "close": "22:45", "food_start": "11:00", "food_end": "22:00", "order_day": False},
        "Wed": {"open": "09:00", "close": "22:45", "food_start": "11:00", "food_end": "22:00", "order_day": False},
        "Thu": {"open": "09:00", "close": "22:45", "food_start": "11:00", "food_end": "22:00", "order_day": False},
        "Fri": {"open": "09:00", "close": "23:30", "food_start": "11:00", "food_end": "23:00", "order_day": False},
        "Sat": {"open": "09:00", "close": "23:30", "food_start": "11:00", "food_end": "23:00", "order_day": False},
        "Sun": {"open": "09:00", "close": "22:45", "food_start": "11:00", "food_end": "22:00", "order_day": False}
    }
}

# ==============================================================================
# GENERIC MASTER STAFF PROFILES (UK FOOD STORE BENCHMARK TEMPLATE)
# ==============================================================================

DEFAULT_STAFF = [
    # MANAGEMENT TIER
    {
        "id": "alex_miller",
        "name": "Alex Miller",
        "role": "General Manager",
        "pay_tier": "Salaried Manager",
        "hourly_rate": 0.00,
        "is_salaried": True,
        "is_keyholder": True,
        "primary_dept": "FOH",
        "skills": ["FOH", "Kitchen", "Grill", "Fryers", "Sets", "Shakes", "Till", "Serve", "Expo", "Prep", "Admin", "Stock"],
        "max_weekly_hours": 45.0,
        "manager_weekly_cap": 45.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Salaried GM (£0 variable marginal cost); Monday 7am food delivery & admin."
    },
    {
        "id": "sam_taylor",
        "name": "Sam Taylor",
        "role": "Assistant Manager",
        "pay_tier": "Assistant Manager (£13.50/h)",
        "hourly_rate": 13.50,
        "is_salaried": False,
        "is_keyholder": True,
        "primary_dept": "FOH",
        "skills": ["FOH", "Kitchen", "Grill", "Till", "Serve", "Shakes", "Expo", "Stock"],
        "max_weekly_hours": 40.0,
        "manager_weekly_cap": 37.5,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Keyholder, customer service lead, food safety lead."
    },
    {
        "id": "jordan_lee",
        "name": "Jordan Lee",
        "role": "Team Leader",
        "pay_tier": "Team Leader (£12.80/h)",
        "hourly_rate": 12.80,
        "is_salaried": False,
        "is_keyholder": True,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Grill", "Fryers", "Sets", "Prep", "FOH", "Till"],
        "max_weekly_hours": 37.5,
        "manager_weekly_cap": 35.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Kitchen supervisor; peak dinner line coordinator."
    },
    {
        "id": "casey_smith",
        "name": "Casey Smith",
        "role": "Team Leader",
        "pay_tier": "Team Leader (£12.50/h)",
        "hourly_rate": 12.50,
        "is_salaried": False,
        "is_keyholder": True,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes", "Expo", "Cashier"],
        "max_weekly_hours": 35.0,
        "manager_weekly_cap": 32.5,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Front-of-house supervisor; close and cash reconciliation lead."
    },

    # EXPERIENCED / SPECIALIST TIER
    {
        "id": "morgan_davis",
        "name": "Morgan Davis",
        "role": "Store Trainer",
        "pay_tier": "Trainer (£12.00/h)",
        "hourly_rate": 12.00,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Grill", "Fryers", "Sets", "Prep"],
        "max_weekly_hours": 35.0,
        "manager_weekly_cap": 35.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Grill station anchor and food quality lead."
    },
    {
        "id": "riley_johnson",
        "name": "Riley Johnson",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Grill", "Fryers", "Sets", "Prep"],
        "max_weekly_hours": 35.0,
        "manager_weekly_cap": 30.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Reliable mid and evening kitchen support."
    },
    {
        "id": "taylor_reed",
        "name": "Taylor Reed",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes", "Expo"],
        "max_weekly_hours": 30.0,
        "manager_weekly_cap": 25.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Daytime FOH specialist."
    },

    # CORE PART-TIME TEAM MEMBERS
    {
        "id": "jamie_wilson",
        "name": "Jamie Wilson",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Fryers", "Sets", "Prep"],
        "max_weekly_hours": 25.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Mid-shift kitchen and prep."
    },
    {
        "id": "chris_murphy",
        "name": "Chris Murphy",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes"],
        "max_weekly_hours": 25.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Front desk, order taking, and dispatch."
    },
    {
        "id": "pat_evans",
        "name": "Pat Evans",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Grill", "Fryers", "Sets"],
        "max_weekly_hours": 25.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Kitchen evening rush and closing maintenance."
    },
    {
        "id": "alex_bailey",
        "name": "Alex Bailey",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes"],
        "max_weekly_hours": 25.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Midday and evening front counter support."
    },

    # WEEKEND & PEAK SUPPORT TIER (STUDENT / PART-TIME)
    {
        "id": "drew_clark",
        "name": "Drew Clark",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes"],
        "max_weekly_hours": 20.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Weekend peak customer support."
    },
    {
        "id": "skyler_white",
        "name": "Skyler White",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Fryers", "Sets", "Prep"],
        "max_weekly_hours": 20.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Weekend kitchen line support."
    },
    {
        "id": "rowan_brooks",
        "name": "Rowan Brooks",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes"],
        "max_weekly_hours": 20.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Peak dinner till operator."
    },
    {
        "id": "cameron_ward",
        "name": "Cameron Ward",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "Kitchen",
        "skills": ["Kitchen", "Grill", "Fryers", "Sets"],
        "max_weekly_hours": 20.0,
        "manager_weekly_cap": 20.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Weekend dinner grill line."
    },
    {
        "id": "avery_cooper",
        "name": "Avery Cooper",
        "role": "Crew Member",
        "pay_tier": "Crew Member (£11.44/h)",
        "hourly_rate": 11.44,
        "is_salaried": False,
        "is_keyholder": False,
        "primary_dept": "FOH",
        "skills": ["FOH", "Till", "Serve", "Shakes"],
        "max_weekly_hours": 16.0,
        "manager_weekly_cap": 16.0,
        "availability": "Any",
        "shift_restriction": "None",
        "global_boundary": "Weekend daytime front support."
    }
]
