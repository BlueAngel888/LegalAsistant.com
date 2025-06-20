from models_gamification import UserProgress, Achievement, ACHIEVEMENTS, init_achievements
from models import db
from datetime import datetime, timedelta
import logging

class GamificationService:
    """Service to handle gamification logic"""
    
    @staticmethod
    def get_or_create_user_progress(session_id):
        """Get or create user progress for a session"""
        progress = UserProgress.query.filter_by(session_id=session_id).first()
        if not progress:
            progress = UserProgress()
            progress.session_id = session_id
            db.session.add(progress)
            db.session.commit()
        return progress
    
    @staticmethod
    def track_document_upload(session_id, file_count=1, is_photo=False, is_multiple=False):
        """Track document upload and check for achievements"""
        progress = GamificationService.get_or_create_user_progress(session_id)
        progress.documents_uploaded += file_count
        progress.last_activity = datetime.utcnow()
        
        earned_achievements = []
        xp_gained = 5 * file_count  # Base XP for uploads
        
        # Check upload count achievements
        upload_achievements = [
            ('first_upload', 1),
            ('upload_5', 5),
            ('upload_10', 10),
            ('upload_25', 25)
        ]
        
        for achievement_id, required_count in upload_achievements:
            if (progress.documents_uploaded >= required_count and 
                achievement_id not in progress.get_achievements()):
                if progress.add_achievement(achievement_id):
                    achievement = Achievement.query.get(achievement_id)
                    if achievement:
                        xp_gained += achievement.xp_reward
                        earned_achievements.append(achievement)
        
        # Check special achievements
        if is_photo and 'photo_scanner' not in progress.get_achievements():
            if progress.add_achievement('photo_scanner'):
                achievement = Achievement.query.get('photo_scanner')
                if achievement:
                    xp_gained += achievement.xp_reward
                    earned_achievements.append(achievement)
        
        if is_multiple and 'multi_upload' not in progress.get_achievements():
            if progress.add_achievement('multi_upload'):
                achievement = Achievement.query.get('multi_upload')
                if achievement:
                    xp_gained += achievement.xp_reward
                    earned_achievements.append(achievement)
        
        # Add XP and check for level up
        level_up, new_level = progress.add_xp(xp_gained)
        
        # Check level achievements
        level_achievements = [
            ('level_5', 5),
            ('level_10', 10),
            ('level_20', 20)
        ]
        
        for achievement_id, required_level in level_achievements:
            if (new_level >= required_level and 
                achievement_id not in progress.get_achievements()):
                if progress.add_achievement(achievement_id):
                    achievement = Achievement.query.get(achievement_id)
                    if achievement:
                        progress.add_xp(achievement.xp_reward)
                        earned_achievements.append(achievement)
        
        db.session.commit()
        
        return {
            'xp_gained': xp_gained,
            'level_up': level_up,
            'new_level': new_level if level_up else progress.user_level,
            'earned_achievements': earned_achievements,
            'progress': progress
        }
    
    @staticmethod
    def track_document_analysis(session_id):
        """Track document analysis completion"""
        progress = GamificationService.get_or_create_user_progress(session_id)
        progress.documents_analyzed += 1
        progress.last_activity = datetime.utcnow()
        
        earned_achievements = []
        xp_gained = 25  # Base XP for analysis
        
        # Check analysis count achievements
        analysis_achievements = [
            ('first_analysis', 1),
            ('analysis_5', 5),
            ('analysis_10', 10)
        ]
        
        for achievement_id, required_count in analysis_achievements:
            if (progress.documents_analyzed >= required_count and 
                achievement_id not in progress.get_achievements()):
                if progress.add_achievement(achievement_id):
                    achievement = Achievement.query.get(achievement_id)
                    if achievement:
                        xp_gained += achievement.xp_reward
                        earned_achievements.append(achievement)
        
        # Add XP and check for level up
        level_up, new_level = progress.add_xp(xp_gained)
        
        # Check level achievements
        level_achievements = [
            ('level_5', 5),
            ('level_10', 10),
            ('level_20', 20)
        ]
        
        for achievement_id, required_level in level_achievements:
            if (new_level >= required_level and 
                achievement_id not in progress.get_achievements()):
                if progress.add_achievement(achievement_id):
                    achievement = Achievement.query.get(achievement_id)
                    if achievement:
                        progress.add_xp(achievement.xp_reward)
                        earned_achievements.append(achievement)
        
        db.session.commit()
        
        return {
            'xp_gained': xp_gained,
            'level_up': level_up,
            'new_level': new_level if level_up else progress.user_level,
            'earned_achievements': earned_achievements,
            'progress': progress
        }
    
    @staticmethod
    def get_user_stats(session_id):
        """Get comprehensive user statistics"""
        progress = GamificationService.get_or_create_user_progress(session_id)
        achievements = [Achievement.query.get(aid) for aid in progress.get_achievements()]
        achievements = [a for a in achievements if a]  # Filter None values
        
        # Calculate next level requirements
        next_level_xp = progress.user_level * 100
        current_level_xp = (progress.user_level - 1) * 100
        progress_to_next = progress.total_xp - current_level_xp
        
        return {
            'level': progress.user_level,
            'total_xp': progress.total_xp,
            'next_level_xp': next_level_xp,
            'progress_to_next': progress_to_next,
            'progress_percentage': progress.get_next_level_progress(),
            'documents_uploaded': progress.documents_uploaded,
            'documents_analyzed': progress.documents_analyzed,
            'achievements': achievements,
            'achievements_count': len(achievements),
            'created_at': progress.created_at
        }
    
    @staticmethod
    def get_leaderboard_data(session_id):
        """Get leaderboard position (simplified for demo)"""
        progress = GamificationService.get_or_create_user_progress(session_id)
        
        # Get top users by XP
        top_users = UserProgress.query.order_by(UserProgress.total_xp.desc()).limit(10).all()
        
        # Find current user position
        user_position = None
        for i, user in enumerate(top_users):
            if user.session_id == session_id:
                user_position = i + 1
                break
        
        # If not in top 10, get approximate position
        if user_position is None:
            higher_xp_count = UserProgress.query.filter(UserProgress.total_xp > progress.total_xp).count()
            user_position = higher_xp_count + 1
        
        return {
            'user_position': user_position,
            'total_users': UserProgress.query.count(),
            'top_users': [{
                'level': user.user_level,
                'total_xp': user.total_xp,
                'documents_uploaded': user.documents_uploaded,
                'is_current_user': user.session_id == session_id
            } for user in top_users]
        }
    
    @staticmethod
    def initialize_gamification():
        """Initialize gamification system with achievements"""
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Initialize achievements
            init_achievements()
            
            logging.info("Gamification system initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize gamification: {str(e)}")
            return False