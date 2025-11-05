from typing import Dict, Any, Optional
import logging
import math

logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user's bisection session"""
    
    def __init__(self, user_id: int, total_frames: int):
        self.user_id = user_id
        self.total_frames = total_frames
        self.left_bound = 0
        self.right_bound = total_frames - 1
        self.steps_taken = 0
        self.found_frame: Optional[int] = None
        self.is_finished = False
        self.current_frame = 0
        self._calculate_next_frame()  # Calculate first frame immediately
    
    def _calculate_next_frame(self):
        """Calculate the next frame to show using binary search"""
        if self.left_bound <= self.right_bound:
            self.current_frame = (self.left_bound + self.right_bound) // 2
            self.steps_taken += 1
            logger.info(f"Calculated frame {self.current_frame} (bounds: {self.left_bound}-{self.right_bound})")
            return True
        return False
    
    def update_bounds(self, has_launched: bool):
        """Update bounds based on user response"""
        logger.info(f"Updating bounds: launched={has_launched}, current_frame={self.current_frame}")
        logger.info(f"Before update - left: {self.left_bound}, right: {self.right_bound}")
        
        if has_launched:
            # Rocket HAS launched - the launch happened at or BEFORE this frame
            # So we need to search in the left half (including current frame)
            self.right_bound = self.current_frame - 1  # Search LEFT of current frame
            logger.info(f"Rocket launched - moving right bound to {self.current_frame - 1}")
        else:
            # Rocket has NOT launched - the launch happened AFTER this frame
            # So we need to search in the right half (excluding current frame)
            self.left_bound = self.current_frame + 1  # Search RIGHT of current frame
            logger.info(f"Rocket not launched - moving left bound to {self.current_frame + 1}")
        
        logger.info(f"After update - left: {self.left_bound}, right: {self.right_bound}")
    
    def next_step(self) -> bool:
        """Move to next step, return True if complete"""
        # Check if search is complete (binary search termination condition)
        if self.left_bound > self.right_bound:
            # Search complete - determine the found frame
            self.is_finished = True
            
            # The launch frame is the first frame where rocket launched
            # Since we're searching for the transition from "no" to "yes",
            # the launch frame should be the left_bound
            if self.left_bound < self.total_frames:
                self.found_frame = self.left_bound
            else:
                self.found_frame = self.total_frames - 1  # Last frame as fallback
            
            logger.info(f"Search complete. Found frame: {self.found_frame}")
            return True
        
        # Continue with next frame
        has_next = self._calculate_next_frame()
        if not has_next:
            self.is_finished = True
            self.found_frame = self.current_frame
            logger.info(f"No next frame available. Using current: {self.found_frame}")
            return True
        
        return False
    
    def is_complete(self) -> bool:
        """Check if bisection is complete"""
        return self.is_finished
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get progress information for user"""
        remaining_steps = self.calculate_remaining_steps()
        total_estimated_steps = self.steps_taken + remaining_steps
        
        # Calculate progress percentage more accurately
        if total_estimated_steps > 0:
            progress_percentage = min(100, int((self.steps_taken / total_estimated_steps) * 100))
        else:
            progress_percentage = 100
        
        return {
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'steps_taken': self.steps_taken,
            'remaining_steps': remaining_steps,
            'progress_percentage': progress_percentage
        }
    
    def calculate_remaining_steps(self) -> int:
        """Calculate estimated remaining steps using binary search complexity"""
        remaining_range = self.right_bound - self.left_bound
        if remaining_range <= 0:
            return 0
        
        # Binary search takes log2(n) steps, so estimate remaining
        return max(0, int(math.log2(remaining_range + 1)))


class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.sessions: Dict[int, UserSession] = {}
    
    def create_session(self, user_id: int, total_frames: int) -> UserSession:
        """Create a new session for user"""
        session = UserSession(user_id, total_frames)
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