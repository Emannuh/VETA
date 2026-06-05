"""
Analytics and reporting utilities for VETA Connect
Generates insights and reports on platform usage and learner performance
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
from abc import ABC, abstractmethod


class AnalyticsBase(ABC):
    """Base class for analytics"""
    
    def __init__(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        self.start_date = start_date or datetime.now() - timedelta(days=30)
        self.end_date = end_date or datetime.now()
    
    @abstractmethod
    def generate_report(self) -> Dict:
        """Generate analytics report"""
        pass


class LearnerAnalytics(AnalyticsBase):
    """Analytics for learner activity and performance"""
    
    def __init__(self, learner=None, start_date=None, end_date=None):
        super().__init__(start_date, end_date)
        self.learner = learner
    
    def calculate_engagement_score(self) -> float:
        """Calculate learner engagement score (0-100)"""
        score = 0
        
        # Profile completeness (20 points)
        if self.learner.bio:
            score += 10
        if self.learner.skills:
            score += 10
        
        # Project activity (30 points)
        projects_count = getattr(self.learner, 'projects', [])
        if projects_count:
            score += min(30, len(list(projects_count)) * 10)
        
        # Interaction (20 points)
        evaluations = getattr(self.learner, 'evaluations', [])
        if evaluations:
            score += min(20, len(list(evaluations)) * 5)
        
        # Badge achievement (30 points)
        badges = getattr(self.learner, 'badges', [])
        if badges:
            score += min(30, len(list(badges)) * 10)
        
        return min(100, score)
    
    def get_activity_summary(self) -> Dict:
        """Get activity summary"""
        projects = getattr(self.learner, 'projects', [])
        evaluations = getattr(self.learner, 'evaluations', [])
        badges = getattr(self.learner, 'badges', [])
        
        return {
            'projects_created': len(list(projects)) if projects else 0,
            'projects_evaluated': len(list(evaluations)) if evaluations else 0,
            'badges_earned': len(list(badges)) if badges else 0,
            'engagement_score': self.calculate_engagement_score(),
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        evaluations = getattr(self.learner, 'evaluations', [])
        
        if not evaluations:
            return {
                'average_rating': 0,
                'ratings_count': 0,
                'best_rating': 0,
                'worst_rating': 0
            }
        
        eval_list = list(evaluations)
        ratings = [e.rating if hasattr(e, 'rating') else 0 for e in eval_list]
        
        return {
            'average_rating': statistics.mean(ratings) if ratings else 0,
            'ratings_count': len(ratings),
            'best_rating': max(ratings) if ratings else 0,
            'worst_rating': min(ratings) if ratings else 0,
            'median_rating': statistics.median(ratings) if ratings else 0,
        }
    
    def get_skill_distribution(self) -> Dict:
        """Get distribution of skills"""
        projects = getattr(self.learner, 'projects', [])
        skill_counter = Counter()
        
        for project in projects:
            skills = getattr(project, 'skills', [])
            for skill in skills:
                skill_counter[str(skill)] += 1
        
        return dict(skill_counter.most_common(10))
    
    def generate_report(self) -> Dict:
        """Generate comprehensive learner report"""
        return {
            'learner_id': self.learner.id if hasattr(self.learner, 'id') else None,
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            },
            'activity_summary': self.get_activity_summary(),
            'performance_metrics': self.get_performance_metrics(),
            'skill_distribution': self.get_skill_distribution(),
        }


class PlatformAnalytics(AnalyticsBase):
    """Analytics for overall platform metrics"""
    
    def __init__(self, queryset_provider, start_date=None, end_date=None):
        super().__init__(start_date, end_date)
        self.queryset_provider = queryset_provider
    
    def get_user_statistics(self) -> Dict:
        """Get user statistics"""
        # Placeholder - would use actual queryset
        return {
            'total_users': 1250,
            'total_learners': 1000,
            'total_trainers': 150,
            'active_users_7d': 800,
            'active_users_30d': 1100,
        }
    
    def get_project_statistics(self) -> Dict:
        """Get project statistics"""
        return {
            'total_projects': 450,
            'projects_evaluated': 350,
            'average_rating': 4.2,
            'projects_created_7d': 45,
            'projects_created_30d': 180,
        }
    
    def get_opportunity_statistics(self) -> Dict:
        """Get opportunity statistics"""
        return {
            'total_opportunities': 42,
            'active_opportunities': 38,
            'total_applications': 520,
            'average_match_score': 78.5,
        }
    
    def get_engagement_trends(self) -> Dict:
        """Get engagement trends"""
        return {
            'daily_active_users': self._get_daily_active_users(),
            'weekly_new_projects': self._get_weekly_projects(),
            'monthly_growth_rate': self._calculate_growth_rate(),
        }
    
    def _get_daily_active_users(self) -> List[Tuple]:
        """Get daily active users"""
        # Placeholder data
        return [(f'Day {i}', 100 + i*10) for i in range(7)]
    
    def _get_weekly_projects(self) -> List[Tuple]:
        """Get weekly new projects"""
        return [(f'Week {i}', 30 + i*5) for i in range(4)]
    
    def _calculate_growth_rate(self) -> float:
        """Calculate month-over-month growth rate"""
        return 15.5  # Placeholder
    
    def generate_report(self) -> Dict:
        """Generate comprehensive platform report"""
        return {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()
            },
            'user_statistics': self.get_user_statistics(),
            'project_statistics': self.get_project_statistics(),
            'opportunity_statistics': self.get_opportunity_statistics(),
            'engagement_trends': self.get_engagement_trends(),
        }


class ReportGenerator:
    """Generates various reports"""
    
    @staticmethod
    def generate_learner_ranking_report(queryset, top_n: int = 100) -> Dict:
        """Generate learner ranking report"""
        rankings = []
        
        for idx, learner in enumerate(queryset[:top_n], 1):
            analytics = LearnerAnalytics(learner)
            rankings.append({
                'rank': idx,
                'learner_name': f'{learner.first_name} {learner.last_name}' if hasattr(learner, 'first_name') else 'Unknown',
                'engagement_score': analytics.calculate_engagement_score(),
                'performance': analytics.get_performance_metrics(),
            })
        
        return {
            'report_type': 'learner_ranking',
            'generated_at': datetime.now().isoformat(),
            'top_learners': rankings
        }
    
    @staticmethod
    def generate_opportunity_effectiveness_report(opportunities_queryset) -> Dict:
        """Generate opportunity effectiveness report"""
        effectiveness_data = []
        
        for opportunity in opportunities_queryset:
            applications = getattr(opportunity, 'applications', [])
            hired = len([a for a in applications if getattr(a, 'hired', False)])
            
            effectiveness_data.append({
                'opportunity_id': opportunity.id if hasattr(opportunity, 'id') else None,
                'title': opportunity.title if hasattr(opportunity, 'title') else 'Unknown',
                'total_applications': len(list(applications)),
                'hired_count': hired,
                'success_rate': (hired / len(list(applications)) * 100) if applications else 0,
            })
        
        return {
            'report_type': 'opportunity_effectiveness',
            'generated_at': datetime.now().isoformat(),
            'data': effectiveness_data
        }
    
    @staticmethod
    def generate_skill_gap_report(learners_queryset) -> Dict:
        """Generate skill gap report"""
        skill_frequency = defaultdict(int)
        skill_demand = defaultdict(int)
        
        for learner in learners_queryset:
            skills = getattr(learner, 'skills', [])
            for skill in skills:
                skill_frequency[str(skill)] += 1
        
        # Simulated demand data
        high_demand_skills = ['Python', 'JavaScript', 'Linux', 'Networking']
        for skill in high_demand_skills:
            skill_demand[skill] = 100
        
        gaps = {}
        for skill, demand in skill_demand.items():
            supply = skill_frequency.get(skill, 0)
            gaps[skill] = {
                'demand': demand,
                'supply': supply,
                'gap': max(0, demand - supply)
            }
        
        return {
            'report_type': 'skill_gap',
            'generated_at': datetime.now().isoformat(),
            'skill_gaps': gaps
        }


class DashboardMetrics:
    """Metrics for dashboard displays"""
    
    @staticmethod
    def get_summary_cards() -> Dict[str, Dict]:
        """Get summary card data"""
        return {
            'total_learners': {
                'value': 1250,
                'change': '+12%',
                'trend': 'up'
            },
            'active_projects': {
                'value': 450,
                'change': '+28%',
                'trend': 'up'
            },
            'avg_rating': {
                'value': 4.2,
                'change': '+0.2',
                'trend': 'up'
            },
            'opportunities': {
                'value': 42,
                'change': '+15%',
                'trend': 'up'
            },
        }
    
    @staticmethod
    def get_activity_chart_data() -> Dict:
        """Get activity chart data"""
        return {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'datasets': [
                {
                    'label': 'New Projects',
                    'data': [12, 19, 8, 15, 22, 18, 25]
                },
                {
                    'label': 'Applications',
                    'data': [5, 10, 8, 12, 14, 11, 16]
                }
            ]
        }
    
    @staticmethod
    def get_trending_skills() -> List[Dict]:
        """Get trending skills"""
        return [
            {'skill': 'Python', 'mentions': 245, 'trend': 'up'},
            {'skill': 'JavaScript', 'mentions': 198, 'trend': 'up'},
            {'skill': 'Linux', 'mentions': 156, 'trend': 'stable'},
            {'skill': 'Networking', 'mentions': 142, 'trend': 'up'},
            {'skill': 'Docker', 'mentions': 89, 'trend': 'up'},
        ]


class ExportService:
    """Export analytics data"""
    
    @staticmethod
    def export_to_csv(report_data: Dict, filename: str = None) -> str:
        """Export report to CSV format"""
        from core.serializers import CSVTransformer
        
        # Flatten report data
        csv_data = CSVTransformer.list_to_csv([report_data])
        return csv_data
    
    @staticmethod
    def export_to_json(report_data: Dict) -> str:
        """Export report to JSON format"""
        from core.serializers import DataSerializer
        
        return DataSerializer.to_json(report_data)
    
    @staticmethod
    def export_to_excel(report_data: Dict, filename: str = None):
        """Export report to Excel format"""
        from core.serializers import ExcelTransformer
        
        # Prepare data as list of dicts
        data = [report_data] if isinstance(report_data, dict) else report_data
        
        excel_bytes = ExcelTransformer.list_to_excel_bytes(data, filename or 'Report')
        return excel_bytes
