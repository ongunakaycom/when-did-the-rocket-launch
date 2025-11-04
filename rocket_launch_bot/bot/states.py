from bernard import layers as lyr
from bernard.platforms.telegram import layers as tgr
from bernard.engine import BaseState


class WelcomeState(BaseState):
    """Initial welcome state"""
    
    async def handle(self) -> None:
        self.send(
            lyr.Text("🚀 Rocket Launch Frame Detector"),
            lyr.Text("I'll help you find the exact frame where the rocket launches!"),
            lyr.Text("I'll show you frames from the video and you tell me if the rocket has launched yet."),
            tgr.InlineKeyboard([
                [tgr.InlineKeyboardCallbackButton("Start Detection", "start")]
            ])
        )


class FrameDisplayState(BaseState):
    """State to display frames and ask for user input"""
    
    async def handle(self) -> None:
        context = await self.request.context.get()
        current_frame = context.get('current_frame', 0)
        total_frames = context.get('total_frames', 0)
        
        self.send(
            lyr.Text(f"Frame {current_frame} of {total_frames}"),
            lyr.Media(await context['frame_data']),
            lyr.Text("Has the rocket launched yet?"),
            tgr.InlineKeyboard([
                [
                    tgr.InlineKeyboardCallbackButton("🚀 Yes", "yes"),
                    tgr.InlineKeyboardCallbackButton("❌ No", "no")
                ]
            ])
        )


class ResultsState(BaseState):
    """Display final results"""
    
    async def handle(self) -> None:
        context = await self.request.context.get()
        launch_frame = context.get('launch_frame')
        
        self.send(
            lyr.Text("🎉 Analysis Complete!"),
            lyr.Text(f"Rocket launch detected at frame: {launch_frame}"),
            lyr.Text("Here's the launch frame:"),
            lyr.Media(await context['final_frame_data']),
            tgr.InlineKeyboard([
                [tgr.InlineKeyboardCallbackButton("Start Over", "restart")]
            ])
        )