from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user's bisection session"""
    
    def __init__(self, user_id: int, total_frames: int):
        self.user_id = user_id
        self.total_frames = total_frames
        self.left_bound = 0
        self.right_bound = total_frames - 1
        self.current_frame = 0
        self.steps_taken = 0
        self.found_frame: Optional[int] = None
    
    def next_step(self) -> bool:
        """Calculate next frame to show, returns True if bisection is complete"""
        if self.left_bound + 1 >= self.right_bound:
            self.found_frame = self.right_bound
            return True
        
        self.current_frame = (self.left_bound + self.right_bound) // 2
        self.steps_taken += 1
        return False
    
    def update_bounds(self, has_launched: bool):
        """Update bounds based on user response"""
        if has_launched:
            self.right_bound = self.current_frame
        else:
            self.left_bound = self.current_frame
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get progress information for user"""
        remaining_steps = self.calculate_remaining_steps()
        return {
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'steps_taken': self.steps_taken,
            'remaining_steps': remaining_steps,
            'progress_percentage': int((self.steps_taken / (self.steps_taken + remaining_steps)) * 100)
        }
    
    def calculate_remaining_steps(self) -> int:
        """Calculate estimated remaining steps"""
        left, right = self.left_bound, self.right_bound
        steps = 0
        while left + 1 < right:
            steps += 1
            mid = (left + right) // 2
            left = mid  # Conservative estimate
        return steps


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.sessions: Dict[int, UserSession] = {}
    
    def create_session(self, user_id: int, total_frames: int) -> UserSession:
        """Create a new session for user"""
        session = UserSession(user_id, total_frames)
        session.next_step()  # Calculate first frame
        self.sessions[user_id] = session
        logger.info(f"Created session for user {user_id}, total frames: {total_frames}")
        return session
    
    def get_session(self, user_id: int) -> Optional[UserSession]:
        """Get user session"""
        return self.sessions.get(user_id)
    
    def end_session(self, user_id: int):
        """End user session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Ended session for user {user_id}")