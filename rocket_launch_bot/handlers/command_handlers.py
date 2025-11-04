import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from bot.framex_client import FrameXClient, FrameProcessor
from bot.session_manager import SessionManager
from config import Config

logger = logging.getLogger(__name__)

# Global instances
frame_client = FrameXClient()
frame_processor = FrameProcessor()
session_manager = SessionManager()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"Start command from user {user.id}")

    try:
        # Get video info
        video_info = await frame_client.get_video_info(Config.VIDEO_NAME)

        # Create user session
        session = session_manager.create_session(user.id, video_info.frames)
        progress = session.get_progress_info()

        # Send welcome message
        welcome_text = (
            "🚀 *Rocket Launch Frame Detector*\n\n"
            "I'll help you find the exact frame where the rocket launches!\n"
            f"• Total frames: {video_info.frames:,}\n"
            f"• Estimated steps: {progress['remaining_steps'] + progress['steps_taken']}\n"
            f"• Current progress: {progress['progress_percentage']}%\n\n"
            "I'll show you frames and you tell me if the rocket has launched yet."
        )

        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown'
        )

        # Show first frame
        await show_current_frame(update, context, session)

    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Sorry, I encountered an error: {str(e)}"
        )


async def show_current_frame(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Show current frame to user"""
    try:
        progress = session.get_progress_info()

        # Get frame image
        frame_data = await frame_client.get_frame_image(Config.VIDEO_NAME, session.current_frame)
        processed_image = await frame_processor.prepare_frame_for_telegram(frame_data)

        # Create caption
        caption = (
            f"📊 *Frame {session.current_frame:,} of {session.total_frames:,}*\n"
            f"🔄 Step {progress['steps_taken']} of ~{progress['remaining_steps'] + progress['steps_taken']}\n"
            f"📈 Progress: {progress['progress_percentage']}%\n\n"
            "*Has the rocket launched yet?* 🚀"
        )

        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🚀 Yes, Rocket Launched", callback_data="yes"),
                InlineKeyboardButton("❌ No, Not Yet", callback_data="no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo with caption and buttons
        if update.callback_query:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(processed_image, caption=caption, parse_mode='Markdown'),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(
                photo=processed_image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing frame: {e}")
        error_msg = "❌ Sorry, I couldn't load the frame. Please try again."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)


async def handle_frame_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user response to frame question"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    response = query.data

    session = session_manager.get_session(user_id)
    if not session:
        await query.edit_message_text("❌ Session expired. Please start again with /start")
        return

    try:
        # Update bounds based on user response
        has_launched = (response == "yes")
        session.update_bounds(has_launched)

        # Check if bisection is complete
        if session.next_step():
            # Bisection complete - show results
            await show_results(update, context, session)
        else:
            # Show next frame
            await show_current_frame(update, context, session)

    except Exception as e:
        logger.error(f"Error handling frame response: {e}")
        await query.edit_message_text("❌ Sorry, I encountered an error. Please try again with /start")


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Show final results"""
    try:
        # Get the launch frame image
        frame_data = await frame_client.get_frame_image(Config.VIDEO_NAME, session.found_frame)
        processed_image = await frame_processor.prepare_frame_for_telegram(frame_data)

        result_text = (
            "🎉 *Analysis Complete!*\n\n"
            f"🚀 *Launch Frame Found:* {session.found_frame:,}\n"
            f"📊 *Total Steps:* {session.steps_taken}\n"
            f"🎯 *Total Frames Analyzed:* {session.total_frames:,}\n\n"
            "*Here's the launch frame:*"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Start Over", callback_data="restart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(processed_image, caption=result_text, parse_mode='Markdown'),
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error showing results: {e}")
        await update.callback_query.edit_message_text(
            f"🎉 Analysis Complete!\n\nLaunch frame: {session.found_frame:,}\n\n"
            "Sorry, I couldn't load the final frame image."
        )


async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle restart request"""
    query = update.callback_query
    await query.answer()

    # End current session
    session_manager.end_session(query.from_user.id)

    # Start new session
    await start_command(update, context)