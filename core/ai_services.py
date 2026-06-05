"""
AI and NLP utilities for VETA Connect
Handles project description summarization, opportunity matching, and intelligent recommendations
"""

import re
from collections import Counter
from typing import List, Dict, Tuple, Optional
import math


class TextProcessor:
    """Processes and analyzes text content"""
    
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'had', 'has', 'have', 'he', 'her', 'hers', 'him', 'his', 'how',
        'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just',
        'me', 'my', 'myself', 'no', 'nor', 'not', 'of', 'on', 'or',
        'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same',
        'she', 'so', 'some', 'such', 'than', 'that', 'the', 'their',
        'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they',
        'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
        'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which',
        'while', 'who', 'whom', 'why', 'will', 'with', 'you', 'your',
        'yours', 'yourself', 'yourselves'
    }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        cleaned = self.clean_text(text)
        return cleaned.split()
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove common stop words"""
        return [t for t in tokens if t not in self.STOP_WORDS and len(t) > 2]
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text"""
        tokens = self.tokenize(text)
        filtered = self.remove_stopwords(tokens)
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)"""
        tokens1 = set(self.remove_stopwords(self.tokenize(text1)))
        tokens2 = set(self.remove_stopwords(self.tokenize(text2)))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0


class ProjectSummarizer:
    """Generates summaries of project descriptions"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def summarize(self, description: str, sentences: int = 3) -> str:
        """Generate a summary of project description"""
        if not description or len(description.strip()) < 50:
            return description
        
        # Split into sentences
        raw_sentences = re.split(r'[.!?]+', description)
        raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        if len(raw_sentences) <= sentences:
            return description
        
        # Score sentences based on keyword frequency
        all_tokens = self.processor.remove_stopwords(
            self.processor.tokenize(description)
        )
        counter = Counter(all_tokens)
        
        sentence_scores = []
        for sent in raw_sentences:
            score = 0
            tokens = self.processor.remove_stopwords(
                self.processor.tokenize(sent)
            )
            for token in tokens:
                score += counter.get(token, 0)
            sentence_scores.append((sent, score))
        
        # Get top sentences
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:sentences]
        top_sentences = sorted(top_sentences, key=lambda x: raw_sentences.index(x[0]))
        
        return '. '.join([s[0] for s in top_sentences]) + '.'
    
    def generate_tags(self, description: str, count: int = 5) -> List[str]:
        """Generate relevant tags from description"""
        keywords = self.processor.extract_keywords(description, top_n=count*2)
        return keywords[:count]


class OpportunityMatcher:
    """Matches learners to opportunities based on skills and interests"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def calculate_match_score(
        self,
        learner_skills: List[str],
        learner_interests: List[str],
        opportunity_requirements: List[str],
        opportunity_description: str
    ) -> float:
        """Calculate match score between learner and opportunity (0-100)"""
        
        skills_score = self._calculate_skill_match(
            learner_skills,
            opportunity_requirements
        )
        
        interest_score = self._calculate_interest_match(
            learner_interests,
            opportunity_description
        )
        
        # Weight: 70% skills, 30% interests
        match_score = (skills_score * 0.7) + (interest_score * 0.3)
        return round(match_score, 2)
    
    def _calculate_skill_match(
        self,
        learner_skills: List[str],
        required_skills: List[str]
    ) -> float:
        """Calculate skill match percentage"""
        if not required_skills:
            return 100.0
        
        learner_skills_lower = [s.lower() for s in learner_skills]
        matched = sum(
            1 for req in required_skills
            if any(req.lower() in ls for ls in learner_skills_lower)
        )
        
        return (matched / len(required_skills)) * 100
    
    def _calculate_interest_match(
        self,
        learner_interests: List[str],
        opportunity_description: str
    ) -> float:
        """Calculate interest match using text similarity"""
        if not learner_interests:
            return 50.0
        
        interests_text = ' '.join(learner_interests)
        similarity = self.processor.calculate_similarity(
            interests_text,
            opportunity_description
        )
        
        return similarity * 100
    
    def find_top_matches(
        self,
        learner_skills: List[str],
        learner_interests: List[str],
        opportunities: List[Dict],
        top_n: int = 5
    ) -> List[Tuple[Dict, float]]:
        """Find top opportunity matches for a learner"""
        scores = []
        
        for opp in opportunities:
            score = self.calculate_match_score(
                learner_skills,
                learner_interests,
                opp.get('requirements', []),
                opp.get('description', '')
            )
            scores.append((opp, score))
        
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n]


class SkillRecommender:
    """Recommends skills based on learner profile and interests"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    SKILL_CATEGORIES = {
        'web_development': [
            'HTML', 'CSS', 'JavaScript', 'React', 'Vue.js', 'Python',
            'Django', 'Flask', 'REST API', 'Git'
        ],
        'mobile_development': [
            'Android', 'iOS', 'React Native', 'Flutter', 'Kotlin', 'Swift'
        ],
        'data_science': [
            'Python', 'SQL', 'Data Analysis', 'Machine Learning', 'Pandas',
            'NumPy', 'Statistics', 'Data Visualization'
        ],
        'ict_support': [
            'Networking', 'System Administration', 'Linux', 'Windows Server',
            'Troubleshooting', 'IT Support'
        ],
        'electrical': [
            'Circuit Design', 'Wiring', 'PLC Programming', 'Electrical Safety',
            'Equipment Installation'
        ],
        'automotive': [
            'Engine Mechanics', 'Diagnostics', 'Welding', 'Sheet Metal Work',
            'Vehicle Maintenance'
        ]
    }
    
    def recommend_skills(
        self,
        current_skills: List[str],
        interests: List[str],
        level: str = 'intermediate'
    ) -> List[str]:
        """Recommend next skills to learn"""
        recommendations = []
        current_lower = [s.lower() for s in current_skills]
        
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                if skill.lower() not in current_lower:
                    # Check relevance to interests
                    interest_match = any(
                        self.processor.calculate_similarity(skill.lower(), i.lower()) > 0.3
                        for i in interests
                    )
                    
                    if interest_match or not interests:
                        recommendations.append(skill)
        
        return list(set(recommendations))[:10]


class LearnerProfileAnalyzer:
    """Analyzes learner profiles for recommendations and insights"""
    
    def __init__(self):
        self.processor = TextProcessor()
        self.matcher = OpportunityMatcher()
        self.recommender = SkillRecommender()
    
    def generate_profile_summary(self, learner_data: Dict) -> Dict:
        """Generate insights about a learner profile"""
        return {
            'completeness': self._calculate_profile_completeness(learner_data),
            'strengths': self._identify_strengths(learner_data),
            'recommendations': self._generate_recommendations(learner_data),
            'career_paths': self._suggest_career_paths(learner_data),
        }
    
    def _calculate_profile_completeness(self, learner_data: Dict) -> float:
        """Calculate profile completeness percentage"""
        required_fields = [
            'first_name', 'last_name', 'email', 'course',
            'skills', 'bio'
        ]
        completed = sum(1 for field in required_fields if learner_data.get(field))
        return (completed / len(required_fields)) * 100
    
    def _identify_strengths(self, learner_data: Dict) -> List[str]:
        """Identify learner strengths from profile"""
        strengths = []
        
        if learner_data.get('projects') and len(learner_data['projects']) >= 3:
            strengths.append('Active Project Contributor')
        
        if learner_data.get('evaluations') and len(learner_data['evaluations']) >= 5:
            strengths.append('Well Evaluated by Trainers')
        
        if learner_data.get('badges'):
            strengths.append(f'Achievement Recognition ({len(learner_data["badges"])} badges)')
        
        return strengths
    
    def _generate_recommendations(self, learner_data: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if not learner_data.get('projects'):
            recommendations.append('Start by uploading your first project')
        
        if len(learner_data.get('bio', '')) < 100:
            recommendations.append('Improve your bio to attract more mentors')
        
        if not learner_data.get('skills'):
            recommendations.append('Add your key technical skills')
        
        return recommendations
    
    def _suggest_career_paths(self, learner_data: Dict) -> List[str]:
        """Suggest relevant career paths"""
        course = learner_data.get('course', '').lower()
        skills = [s.lower() for s in learner_data.get('skills', [])]
        
        paths = []
        
        if 'ict' in course or any(s in ['python', 'java', 'javascript'] for s in skills):
            paths.append('Software Development')
        
        if 'electrical' in course:
            paths.append('Electrical Engineering')
        
        if 'automotive' in course:
            paths.append('Automotive Engineering')
        
        if 'hospitality' in course:
            paths.append('Hospitality Management')
        
        return paths if paths else ['General Technical Track']
