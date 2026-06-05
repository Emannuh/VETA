"""
Custom validators for VETA Connect platform
Handles validation of learner data, projects, applications, and more
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class EmailValidator:
    """Validates email addresses with additional checks"""
    
    def __init__(self, whitelist_domains=None):
        self.whitelist_domains = whitelist_domains or []
    
    def validate(self, email):
        """Validate email format and optionally against whitelist"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(_('Invalid email format'))
        
        if self.whitelist_domains:
            domain = email.split('@')[1]
            if domain not in self.whitelist_domains:
                raise ValidationError(
                    _('Email domain not in whitelist')
                )
    
    def __call__(self, value):
        self.validate(value)


class KenyanPhoneValidator:
    """Validates Kenyan phone numbers"""
    
    PREFIXES = {
        '254701', '254702', '254703', '254704', '254705', '254706', 
        '254707', '254708', '254709', '254710', '254711', '254712',
        '254713', '254714', '254715', '254716', '254717', '254718',
        '254719', '254720', '254721', '254722', '254723', '254724',
        '254725', '254726', '254727', '254728', '254729', '254730',
        '254731', '254732', '254733', '254734', '254735', '254736',
        '254737', '254738', '254739', '254740',
    }
    
    def validate(self, phone_number):
        """Validate Kenyan phone number"""
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)\.]+', '', phone_number)
        
        # Check if valid Kenyan format
        if not clean_phone.startswith('254') and not clean_phone.startswith('+254'):
            if clean_phone.startswith('0'):
                clean_phone = '254' + clean_phone[1:]
            else:
                raise ValidationError(_('Invalid phone number format'))
        
        # Normalize to international format
        if clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        
        if len(clean_phone) != 12:
            raise ValidationError(_('Phone number must be 12 digits (including country code)'))
        
        if not clean_phone[:6] in self.PREFIXES:
            raise ValidationError(_('Invalid Kenyan phone number prefix'))
    
    def __call__(self, value):
        self.validate(value)


class CourseCodeValidator:
    """Validates TVET course codes"""
    
    def validate(self, code):
        """Validate course code format (e.g., ICT-001, ELX-025)"""
        pattern = r'^[A-Z]{2,4}-\d{3}$'
        if not re.match(pattern, code):
            raise ValidationError(
                _('Invalid course code. Use format: XXX-### (e.g., ICT-001)')
            )
    
    def __call__(self, value):
        self.validate(value)


class ProjectDescriptionValidator:
    """Validates project descriptions for quality"""
    
    MIN_LENGTH = 50
    MAX_LENGTH = 5000
    
    def validate(self, description):
        """Ensure description meets quality standards"""
        if not description or len(description.strip()) < self.MIN_LENGTH:
            raise ValidationError(
                _('Project description must be at least %(min)d characters long'),
                code='min_length',
                params={'min': self.MIN_LENGTH}
            )
        
        if len(description) > self.MAX_LENGTH:
            raise ValidationError(
                _('Project description cannot exceed %(max)d characters'),
                code='max_length',
                params={'max': self.MAX_LENGTH}
            )
        
        # Check for spam-like patterns
        if description.count(' ') / len(description) < 0.15:
            raise ValidationError(
                _('Description appears to be spam or improperly formatted')
            )
    
    def __call__(self, value):
        self.validate(value)


class SkillValidator:
    """Validates skill tags"""
    
    RESERVED_SKILLS = {
        'all', 'none', 'admin', 'staff', 'trainer', 'learner'
    }
    
    def validate(self, skill):
        """Validate individual skill"""
        skill_lower = skill.lower().strip()
        
        if skill_lower in self.RESERVED_SKILLS:
            raise ValidationError(
                _('This skill name is reserved and cannot be used')
            )
        
        if not re.match(r'^[a-zA-Z0-9\s\+\#\.\-]{2,50}$', skill):
            raise ValidationError(
                _('Skill must be 2-50 characters and contain only letters, numbers, and basic symbols')
            )
    
    def __call__(self, value):
        self.validate(value)


class RatingValidator:
    """Validates ratings and evaluations"""
    
    def validate_score(self, score, min_val=0, max_val=5):
        """Validate numeric rating score"""
        try:
            float_score = float(score)
            if float_score < min_val or float_score > max_val:
                raise ValidationError(
                    _('Rating must be between %(min)d and %(max)d'),
                    params={'min': min_val, 'max': max_val}
                )
        except (TypeError, ValueError):
            raise ValidationError(_('Rating must be a valid number'))
    
    def __call__(self, value):
        self.validate_score(value)
