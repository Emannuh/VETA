"""
Email and notification utilities for VETA Connect
Handles sending emails, SMS, and in-app notifications
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import List, Dict, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class NotificationBase(ABC):
    """Base class for notifications"""
    
    def __init__(self, recipient, subject: str, context: Dict = None):
        self.recipient = recipient
        self.subject = subject
        self.context = context or {}
        self.created_at = datetime.now()
    
    @abstractmethod
    def send(self) -> bool:
        """Send notification"""
        pass


class EmailNotification(NotificationBase):
    """Email notification"""
    
    def __init__(
        self,
        recipient_email: str,
        subject: str,
        template_name: str,
        context: Dict = None,
        from_email: str = 'noreply@vetaconnect.com'
    ):
        super().__init__(recipient_email, subject, context)
        self.template_name = template_name
        self.from_email = from_email
        self.html_content = None
        self.text_content = None
    
    def render_template(self):
        """Render email template"""
        try:
            self.html_content = render_to_string(self.template_name, self.context)
            self.text_content = strip_tags(self.html_content)
        except Exception as e:
            print(f'Error rendering template: {e}')
            return False
        return True
    
    def send(self, fail_silently: bool = False) -> bool:
        """Send email notification"""
        if not self.render_template():
            return False
        
        try:
            msg = EmailMultiAlternatives(
                subject=self.subject,
                body=self.text_content,
                from_email=self.from_email,
                to=[self.recipient]
            )
            msg.attach_alternative(self.html_content, 'text/html')
            msg.send(fail_silently=fail_silently)
            return True
        except Exception as e:
            print(f'Error sending email: {e}')
            return False


class BulkEmailNotification:
    """Send emails to multiple recipients"""
    
    def __init__(self, subject: str, template_name: str, from_email: str = 'noreply@vetaconnect.com'):
        self.subject = subject
        self.template_name = template_name
        self.from_email = from_email
        self.recipients = []
    
    def add_recipient(self, email: str, context: Dict = None):
        """Add recipient"""
        self.recipients.append((email, context or {}))
        return self
    
    def add_recipients(self, recipients_data: List[Dict]):
        """Add multiple recipients"""
        for data in recipients_data:
            email = data.get('email')
            context = data.get('context', {})
            self.recipients.append((email, context))
        return self
    
    def send(self, fail_silently: bool = False) -> Dict:
        """Send emails to all recipients"""
        results = {
            'total': len(self.recipients),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for email, context in self.recipients:
            notification = EmailNotification(
                recipient_email=email,
                subject=self.subject,
                template_name=self.template_name,
                context=context,
                from_email=self.from_email
            )
            
            if notification.send(fail_silently=fail_silently):
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({'email': email, 'error': 'Failed to send'})
        
        return results


class NotificationBuilder:
    """Builder for creating notifications"""
    
    TEMPLATES = {
        'welcome': 'emails/welcome.html',
        'project_evaluated': 'emails/project_evaluated.html',
        'badge_awarded': 'emails/badge_awarded.html',
        'opportunity_match': 'emails/opportunity_match.html',
        'mentor_request': 'emails/mentor_request.html',
        'password_reset': 'emails/password_reset.html',
    }
    
    SUBJECTS = {
        'welcome': 'Welcome to VETA Connect!',
        'project_evaluated': 'Your project has been evaluated',
        'badge_awarded': 'Congratulations! You earned a badge',
        'opportunity_match': 'New opportunity matched for you',
        'mentor_request': 'New mentor request',
        'password_reset': 'Reset your password',
    }
    
    @classmethod
    def build_welcome_email(cls, user_email: str, user_name: str) -> EmailNotification:
        """Build welcome email"""
        return EmailNotification(
            recipient_email=user_email,
            subject=cls.SUBJECTS['welcome'],
            template_name=cls.TEMPLATES['welcome'],
            context={'user_name': user_name}
        )
    
    @classmethod
    def build_project_evaluated_email(
        cls,
        user_email: str,
        user_name: str,
        project_title: str,
        rating: float
    ) -> EmailNotification:
        """Build project evaluated email"""
        return EmailNotification(
            recipient_email=user_email,
            subject=cls.SUBJECTS['project_evaluated'],
            template_name=cls.TEMPLATES['project_evaluated'],
            context={
                'user_name': user_name,
                'project_title': project_title,
                'rating': rating
            }
        )
    
    @classmethod
    def build_badge_awarded_email(
        cls,
        user_email: str,
        user_name: str,
        badge_name: str,
        badge_icon: str
    ) -> EmailNotification:
        """Build badge awarded email"""
        return EmailNotification(
            recipient_email=user_email,
            subject=cls.SUBJECTS['badge_awarded'],
            template_name=cls.TEMPLATES['badge_awarded'],
            context={
                'user_name': user_name,
                'badge_name': badge_name,
                'badge_icon': badge_icon
            }
        )
    
    @classmethod
    def build_opportunity_match_email(
        cls,
        user_email: str,
        user_name: str,
        opportunity_title: str,
        match_score: float
    ) -> EmailNotification:
        """Build opportunity match email"""
        return EmailNotification(
            recipient_email=user_email,
            subject=cls.SUBJECTS['opportunity_match'],
            template_name=cls.TEMPLATES['opportunity_match'],
            context={
                'user_name': user_name,
                'opportunity_title': opportunity_title,
                'match_score': match_score
            }
        )


class InAppNotification:
    """In-app notification"""
    
    def __init__(self, user, title: str, message: str, notification_type: str = 'info'):
        self.user = user
        self.title = title
        self.message = message
        self.notification_type = notification_type  # info, success, warning, error
        self.created_at = datetime.now()
        self.read = False
        self.action_url = None
        self.action_text = None
    
    def set_action(self, url: str, text: str = 'View'):
        """Set action link"""
        self.action_url = url
        self.action_text = text
        return self
    
    def to_dict(self) -> Dict:
        """Convert to dict"""
        return {
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'action': {
                'url': self.action_url,
                'text': self.action_text
            } if self.action_url else None
        }


class NotificationQueue:
    """Queue for notifications"""
    
    def __init__(self):
        self.queue = []
    
    def add(self, notification: NotificationBase):
        """Add notification to queue"""
        self.queue.append(notification)
        return self
    
    def send_all(self, fail_silently: bool = False) -> Dict:
        """Send all notifications in queue"""
        results = {
            'total': len(self.queue),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for notification in self.queue:
            try:
                if notification.send(fail_silently=fail_silently):
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        self.queue.clear()
        return results
    
    def clear(self):
        """Clear queue"""
        self.queue.clear()


class SMSNotification(NotificationBase):
    """SMS notification (placeholder for SMS service integration)"""
    
    def __init__(self, phone_number: str, message: str):
        super().__init__(phone_number, '', {'message': message})
        self.message = message
        self.phone_number = phone_number
    
    def send(self) -> bool:
        """Send SMS notification"""
        # Implement with your SMS service (Twilio, Africa's Talking, etc.)
        try:
            # Placeholder for actual SMS sending
            print(f'SMS to {self.phone_number}: {self.message}')
            return True
        except Exception as e:
            print(f'Error sending SMS: {e}')
            return False


class PushNotification(NotificationBase):
    """Push notification"""
    
    def __init__(self, user, title: str, body: str, data: Dict = None):
        super().__init__(user, title, {'body': body, 'data': data or {}})
        self.body = body
        self.data = data or {}
    
    def send(self) -> bool:
        """Send push notification"""
        # Implement with your push service (Firebase, OneSignal, etc.)
        try:
            # Placeholder for actual push sending
            print(f'Push to {self.recipient}: {self.subject} - {self.body}')
            return True
        except Exception as e:
            print(f'Error sending push: {e}')
            return False


class NotificationService:
    """Central notification service"""
    
    def __init__(self):
        self.queue = NotificationQueue()
    
    def notify_project_evaluation(self, user, project, rating, feedback):
        """Notify user about project evaluation"""
        notification = NotificationBuilder.build_project_evaluated_email(
            user.email,
            user.first_name,
            project.title,
            rating
        )
        return notification.send()
    
    def notify_badge_earned(self, user, badge):
        """Notify user about badge"""
        notification = NotificationBuilder.build_badge_awarded_email(
            user.email,
            user.first_name,
            badge.name,
            badge.icon
        )
        return notification.send()
    
    def notify_opportunity_match(self, user, opportunity, match_score):
        """Notify user about matching opportunity"""
        notification = NotificationBuilder.build_opportunity_match_email(
            user.email,
            user.first_name,
            opportunity.title,
            match_score
        )
        return notification.send()
    
    def notify_mentor_request(self, mentor_user, trainee_user):
        """Notify mentor about request"""
        email_context = {
            'mentor_name': mentor_user.first_name,
            'trainee_name': trainee_user.first_name,
            'trainee_profile_url': f'/profiles/{trainee_user.id}/'
        }
        
        notification = EmailNotification(
            recipient_email=mentor_user.email,
            subject=NotificationBuilder.SUBJECTS['mentor_request'],
            template_name=NotificationBuilder.TEMPLATES['mentor_request'],
            context=email_context
        )
        return notification.send()
