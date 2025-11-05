# Rocket Launch Bot - Architecture & Development Process

## System Architecture Overview

### Core Components Structure

```
rocket_launch_bot/
├── config.py
├── main.py
├── bot/
│   ├── framex_client.py
│   └── session_manager.py
└── handlers/
    └── command_handlers.py
```

## Architectural Decisions

### 1. Modular Design Pattern
- **Separation of Concerns**: Each module has single responsibility
- **Independent Testing**: Components can be tested in isolation
- **Maintainability**: Clear boundaries between system parts

### 2. Configuration Management

```python
# config.py - Centralized configuration
class Config:
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    API_BASE: str = os.getenv("API_BASE")
    VIDEO_NAME: str = os.getenv("VIDEO_NAME")
```

## Core Logic Implementation

### 3. Binary Search Algorithm

```python
# session_manager.py - Bisection logic
class UserSession:
    def update_bounds(self, has_launched: bool):
        if has_launched:
            # Rocket launched - search left half
            self.right_bound = self.current_frame - 1
        else:
            # Rocket not launched - search right half
            self.left_bound = self.current_frame + 1
```

### 4. Telegram Bot Integration

```python
# command_handlers.py - User interaction
async def handle_frame_response(update: Update, context: CallbackContext):
    response = update.callback_query.data
    session.update_bounds(response == "yes")
    session.next_step()
```

## Development Process

### 5. Error Handling Strategy
- **Graceful Degradation**: Fallback mechanisms for API failures
- **User Feedback**: Clear error messages with recovery options
- **Logging**: Comprehensive logging for debugging

### 6. Session Management

```python
# session_manager.py - State management
class SessionManager:
    def create_session(self, user_id: int, total_frames: int)
    def get_session(self, user_id: int)
    def end_session(self, user_id: int)
```

## API Integration Layer

### 7. FrameX Client Design

```python
# framex_client.py - External API abstraction
class FrameXClient:
    def get_video_info(self, video_name: str) -> VideoInfo
    def get_frame_image(self, video_name: str, frame_number: int) -> bytes
```

### 8. Image Processing Pipeline

```python
# framex_client.py - Media optimization
class FrameProcessor:
    def prepare_frame_for_telegram(self, image_data: bytes) -> bytes
```

## User Experience Design

### 9. Interactive Interface
- **Inline Keyboards**: Yes/No buttons for binary responses
- **Progress Tracking**: Step counter and percentage completion
- **Visual Feedback**: Frame numbers and timeline context

### 10. State Recovery
- **Session Persistence**: Maintain search state across interactions
- **Restart Capability**: Clean session reset functionality
- **Error Recovery**: Graceful handling of network failures

## Performance Considerations

### 11. Efficient Frame Loading
- **Lazy Loading**: Load frames only when needed
- **Image Optimization**: Resize and compress for Telegram
- **Caching Strategy**: Session-based frame caching

### 12. Scalability Design
- **Stateless Components**: Minimal shared state between requests
- **Resource Management**: Proper connection pooling and cleanup
- **Concurrent Users**: Session isolation for multiple users

## Testing Strategy

### 13. Testable Architecture
- **Dependency Injection**: Mockable external dependencies
- **Unit Test Coverage**: Isolated component testing
- **Integration Tests**: End-to-end workflow validation

## Deployment Architecture

### 14. Environment Configuration

```python
# config.py - Environment-based settings
@classmethod
def validate(cls) -> Optional[str]:
    if not cls.BOT_TOKEN:
        return "TELEGRAM_BOT_TOKEN required"
```

### 15. Monitoring & Logging
- **Structured Logging**: JSON-formatted logs for analysis
- **Error Tracking**: Comprehensive exception handling
- **Performance Metrics**: Response time and success rate tracking