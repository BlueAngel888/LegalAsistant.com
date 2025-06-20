from models import db
from datetime import datetime
import json

class UserProgress(db.Model):
    """Model to track user gamification progress"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    session_id = db.Column(db.String(255), nullable=False, unique=True)
    user_level = db.Column(db.Integer, default=1)
    total_xp = db.Column(db.Integer, default=0)
    documents_uploaded = db.Column(db.Integer, default=0)
    documents_analyzed = db.Column(db.Integer, default=0)
    achievements_earned = db.Column(db.Text, default='[]')  # JSON array of achievement IDs
    streak_days = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def add_achievement(self, achievement_id):
        """Add an achievement to the user's collection"""
        achievements = json.loads(self.achievements_earned or '[]')
        if achievement_id not in achievements:
            achievements.append(achievement_id)
            self.achievements_earned = json.dumps(achievements)
            return True
        return False
    
    def get_achievements(self):
        """Get list of earned achievements"""
        return json.loads(self.achievements_earned or '[]')
    
    def add_xp(self, points):
        """Add XP and check for level up"""
        old_level = self.user_level
        self.total_xp += points
        
        # Level calculation: every 100 XP = 1 level
        new_level = (self.total_xp // 100) + 1
        level_up = new_level > old_level
        self.user_level = new_level
        
        return level_up, new_level
    
    def get_next_level_progress(self):
        """Get progress towards next level as percentage"""
        current_level_xp = (self.user_level - 1) * 100
        next_level_xp = self.user_level * 100
        progress_xp = self.total_xp - current_level_xp
        return min(100, (progress_xp / 100) * 100)

class Achievement(db.Model):
    """Model to define available achievements"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False)  # Icon class or emoji
    xp_reward = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=False)  # upload, analysis, streak, etc.
    requirement_type = db.Column(db.String(50), nullable=False)  # count, streak, special
    requirement_value = db.Column(db.Integer, default=1)
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Achievement definitions
ACHIEVEMENTS = [
    # Upload achievements
    {
        'id': 'first_upload',
        'name': 'First Steps',
        'description': 'Upload your first document',
        'icon': '📄',
        'xp_reward': 10,
        'category': 'upload',
        'requirement_type': 'count',
        'requirement_value': 1,
        'rarity': 'common'
    },
    {
        'id': 'upload_5',
        'name': 'Getting Started',
        'description': 'Upload 5 documents',
        'icon': '📚',
        'xp_reward': 25,
        'category': 'upload',
        'requirement_type': 'count',
        'requirement_value': 5,
        'rarity': 'common'
    },
    {
        'id': 'upload_10',
        'name': 'Document Collector',
        'description': 'Upload 10 documents',
        'icon': '🗂️',
        'xp_reward': 50,
        'category': 'upload',
        'requirement_type': 'count',
        'requirement_value': 10,
        'rarity': 'rare'
    },
    {
        'id': 'upload_25',
        'name': 'Power User',
        'description': 'Upload 25 documents',
        'icon': '💼',
        'xp_reward': 100,
        'category': 'upload',
        'requirement_type': 'count',
        'requirement_value': 25,
        'rarity': 'epic'
    },
    # Analysis achievements
    {
        'id': 'first_analysis',
        'name': 'Legal Eagle',
        'description': 'Complete your first document analysis',
        'icon': '🦅',
        'xp_reward': 20,
        'category': 'analysis',
        'requirement_type': 'count',
        'requirement_value': 1,
        'rarity': 'common'
    },
    {
        'id': 'analysis_5',
        'name': 'Case Solver',
        'description': 'Complete 5 document analyses',
        'icon': '🔍',
        'xp_reward': 75,
        'category': 'analysis',
        'requirement_type': 'count',
        'requirement_value': 5,
        'rarity': 'rare'
    },
    {
        'id': 'analysis_10',
        'name': 'Legal Expert',
        'description': 'Complete 10 document analyses',
        'icon': '⚖️',
        'xp_reward': 150,
        'category': 'analysis',
        'requirement_type': 'count',
        'requirement_value': 10,
        'rarity': 'epic'
    },
    # Level achievements
    {
        'id': 'level_5',
        'name': 'Rising Star',
        'description': 'Reach level 5',
        'icon': '⭐',
        'xp_reward': 50,
        'category': 'level',
        'requirement_type': 'level',
        'requirement_value': 5,
        'rarity': 'rare'
    },
    {
        'id': 'level_10',
        'name': 'Legal Scholar',
        'description': 'Reach level 10',
        'icon': '🎓',
        'xp_reward': 100,
        'category': 'level',
        'requirement_type': 'level',
        'requirement_value': 10,
        'rarity': 'epic'
    },
    {
        'id': 'level_20',
        'name': 'Master Analyst',
        'description': 'Reach level 20',
        'icon': '👑',
        'xp_reward': 200,
        'category': 'level',
        'requirement_type': 'level',
        'requirement_value': 20,
        'rarity': 'legendary'
    },
    # Special achievements
    {
        'id': 'photo_scanner',
        'name': 'Scanner Pro',
        'description': 'Use the document scanner feature',
        'icon': '📱',
        'xp_reward': 30,
        'category': 'special',
        'requirement_type': 'special',
        'requirement_value': 1,
        'rarity': 'rare'
    },
    {
        'id': 'multi_upload',
        'name': 'Multitasker',
        'description': 'Upload multiple files at once',
        'icon': '🔄',
        'xp_reward': 15,
        'category': 'special',
        'requirement_type': 'special',
        'requirement_value': 1,
        'rarity': 'common'
    }
]

def init_achievements():
    """Initialize achievements in the database"""
    with db.session.begin():
        for achievement_data in ACHIEVEMENTS:
            existing = Achievement.query.get(achievement_data['id'])
            if not existing:
                achievement = Achievement(**achievement_data)
                db.session.add(achievement)