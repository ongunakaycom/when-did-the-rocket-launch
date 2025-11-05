import logging
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from bot.framex_client import FrameXClient, FrameProcessor
from bot.session_manager import SessionManager
from config import Config

logger = logging.getLogger(__name__)

# Global instances
frame_client = FrameXClient()
frame_processor = FrameProcessor()
session_manager = SessionManager()

async def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"Start command from user {user.id}")

    try:
        # Clean up any existing session first
        session_manager.end_session(user.id)
        
        # Get video info
        video_info = frame_client.get_video_info(Config.VIDEO_NAME)

        # Create user session
        session = session_manager.create_session(user.id, video_info.frames)
        progress = session.get_progress_info()

        # Send MUCH CLEARER welcome message
        welcome_text = (
            "🚀 *Rocket Launch Frame Detector*\n\n"
            "I'll help you find the exact frame where the Falcon Heavy rocket LAUNCHES!\n"
            f"• Total frames: {video_info.frames:,}\n"
            f"• Estimated steps: {progress['remaining_steps'] + progress['steps_taken']}\n\n"
            "🔴 *CRITICAL: What to look for:*\n"
            "• ❌ NO: SpaceX studio, hosts talking, countdown, static rocket on pad\n"
            "• ❌ NO: Tesla Roadster in space (this happens AFTER launch)\n"
            "• ✅ YES: ONLY when you see FIRE/SMOKE and the rocket MOVING UPWARD from the launch pad\n\n"
            "The video shows: PRE-LAUNCH → COUNTDOWN → ACTUAL LAUNCH → IN-FLIGHT → TESLA IN SPACE\n"
            "We're looking for the EXACT moment of LAUNCH (fire + upward movement)!"
        )

        # Handle both message and callback_query scenarios
        if update.message:
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown'
            )
            # Show first frame
            await show_current_frame(update, context, session)
        elif update.callback_query:
            # For callback queries, we need to handle both text and photo messages
            try:
                # Try to edit as caption first (if it's a photo message)
                await update.callback_query.edit_message_caption(
                    caption=welcome_text,
                    parse_mode='Markdown'
                )
            except BadRequest:
                # If that fails, edit as text
                await update.callback_query.edit_message_text(
                    welcome_text,
                    parse_mode='Markdown'
                )
            # Show first frame after a brief delay
            await show_current_frame(update, context, session)

    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
        if update.message:
            await update.message.reply_text(error_msg)
        elif update.callback_query:
            try:
                await update.callback_query.edit_message_text(error_msg)
            except BadRequest:
                await update.callback_query.edit_message_caption(caption=error_msg)

async def show_current_frame(update: Update, context: CallbackContext, session=None):
    """Show current frame to user"""
    if session is None:
        user_id = update.effective_user.id
        session = session_manager.get_session(user_id)
        if not session:
            await handle_session_expired(update, context)
            return

    try:
        progress = session.get_progress_info()

        # Get frame image
        frame_data = frame_client.get_frame_image(Config.VIDEO_NAME, session.current_frame)
        processed_image = frame_processor.prepare_frame_for_telegram(frame_data)

        # Add timeline guidance to help users understand where they are
        timeline_info = _get_timeline_info(session.current_frame, session.total_frames)

        # Create MUCH CLEARER caption
        caption = (
            f"📊 *Frame {session.current_frame:,} of {session.total_frames:,}*\n"
            f"{timeline_info}\n"
            f"🔄 Step {progress['steps_taken']} of ~{progress['remaining_steps'] + progress['steps_taken']}\n"
            f"📈 Progress: {progress['progress_percentage']}%\n\n"
            "*Has the rocket LAUNCHED yet?* 🚀\n"
            "✅ YES: Only if you see FIRE/SMOKE and UPWARD MOVEMENT\n"
            "❌ NO: For everything else (studio, countdown, Tesla in space)"
        )

        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("🚀 YES - Rocket Launched", callback_data="yes"),
                InlineKeyboardButton("❌ NO - Not Yet", callback_data="no")
            ],
            [InlineKeyboardButton("🔄 Restart", callback_data="restart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo with caption and buttons
        if update.callback_query:
            try:
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(processed_image, caption=caption, parse_mode='Markdown'),
                    reply_markup=reply_markup
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    # Message is the same, ignore the error
                    logger.info("Message not modified (same content), continuing...")
                else:
                    raise e
        else:
            await update.message.reply_photo(
                photo=processed_image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing frame {session.current_frame if session else 'unknown'}: {e}", exc_info=True)
        error_msg = (
            "❌ Sorry, I couldn't load the frame. "
            "This might be due to network issues or the frame being unavailable.\n\n"
            "Please try again with /start"
        )
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(error_msg)
            except Exception as edit_error:
                logger.error(f"Error editing message: {edit_error}")
                # If editing fails, send a new message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_msg
                )
        else:
            await update.message.reply_text(error_msg)

def _get_timeline_info(current_frame: int, total_frames: int) -> str:
    """Provide timeline guidance based on current frame position"""
    if current_frame < 15000:
        return "📍 *You're in: EARLY PRE-LAUNCH* (SpaceX studio, hosts talking)"
    elif current_frame < 35000:
        return "📍 *You're in: COUNTDOWN PHASE* (rocket on pad, countdown graphics)"
    elif current_frame < 48000:
        return "📍 *You're in: PRE-LAUNCH FINAL* (rocket on pad, final preparations)"
    elif current_frame < 52000:
        return "📍 *You're in: LAUNCH WINDOW* (watch closely for FIRE and SMOKE!)"
    elif current_frame < 56000:
        return "📍 *You're in: LAUNCH MOMENT* (should see fire/smoke + upward movement)"
    elif current_frame < 60000:
        return "📍 *You're in: POST-LAUNCH* (rocket ascending, stage separation)"
    else:
        return "📍 *You're in: IN-FLIGHT* (Tesla Roadster in space - this is AFTER launch)"

async def handle_frame_response(update: Update, context: CallbackContext):
    """Handle user response to frame question"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    response = query.data

    logger.info(f"User {user_id} responded: {response}")

    # Handle restart first
    if response == "restart":
        await handle_restart(update, context)
        return

    # Validate response
    if response not in ['yes', 'no']:
        logger.warning(f"Invalid response received: {response}")
        await query.edit_message_text("❌ Invalid response. Please use the buttons provided.")
        return

    session = session_manager.get_session(user_id)
    if not session:
        await handle_session_expired(update, context)
        return

    try:
        # Update bounds based on user response
        has_launched = (response == "yes")
        logger.info(f"User {user_id} at frame {session.current_frame}: launched={has_launched}")
        
        session.update_bounds(has_launched)

        # Move to next step and check if complete
        is_complete = session.next_step()
        
        if is_complete:
            # Bisection complete - show results
            if session.found_frame is None:
                logger.error(f"Session complete but found_frame is None for user {user_id}")
                # Fallback: use the last frame we showed
                session.found_frame = session.current_frame
            
            logger.info(f"Session complete for user {user_id}. Found frame: {session.found_frame}")
            await show_results(update, context, session)
            session_manager.end_session(user_id)
        else:
            # Continue to next frame
            await show_current_frame(update, context, session)

    except Exception as e:
        logger.error(f"Error handling frame response: {e}", exc_info=True)
        try:
            await query.edit_message_text("❌ Sorry, I encountered an error. Please try again with /start")
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")
            await context.bot.send_message(
                chat_id=user_id, 
                text="❌ Sorry, I encountered an error. Please try again with /start"
            )

async def show_results(update: Update, context: CallbackContext, session):
    """Show final results"""
    try:
        # Ensure found_frame is valid
        if session.found_frame is None or session.found_frame < 0:
            logger.error(f"Invalid found_frame: {session.found_frame}, using fallback")
            session.found_frame = session.total_frames - 1  # Use last frame as fallback

        # Calculate approximate time (frames to time conversion)
        # Frame rate: 30000/1001 ≈ 29.97 fps
        frame_rate = 30000 / 1001  # ~29.97 frames per second
        time_in_seconds = session.found_frame / frame_rate
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)

        # Create result text
        result_text = (
            "🎉 *Analysis Complete!*\n\n"
            f"🚀 *Launch Frame Found:* {session.found_frame:,}\n"
            f"⏱️ *Approximate Time:* {minutes}m {seconds}s\n"
            f"📊 *Total Steps:* {session.steps_taken}\n"
            f"🎯 *Total Frames Analyzed:* {session.total_frames:,}\n\n"
            "*Here's the launch frame:*"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Start Over", callback_data="restart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            # Get the launch frame image
            frame_data = frame_client.get_frame_image(Config.VIDEO_NAME, session.found_frame)
            processed_image = frame_processor.prepare_frame_for_telegram(frame_data)

            # Try to edit the message with the new image and caption
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(processed_image, caption=result_text, parse_mode='Markdown'),
                reply_markup=reply_markup
            )
            
        except Exception as image_error:
            logger.error(f"Error loading launch frame image: {image_error}")
            # If image fails, just show the text results
            await update.callback_query.edit_message_text(
                result_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing results: {e}", exc_info=True)
        # Fallback: send text-only results
        try:
            result_text = (
                "🎉 *Analysis Complete!*\n\n"
                f"🚀 *Launch Frame Found:* {session.found_frame:,}\n"
                f"📊 *Total Steps:* {session.steps_taken}\n"
                f"🎯 *Total Frames Analyzed:* {session.total_frames:,}\n\n"
                "📸 *Note:* Could not load the launch frame image, but the analysis is complete!"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Start Over", callback_data="restart")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                result_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as final_error:
            logger.error(f"Final fallback also failed: {final_error}")
            # Last resort
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎉 Analysis complete! Launch frame: {session.found_frame:,}",
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"Error showing results: {e}", exc_info=True)
        # Enhanced fallback with more information
        result_text = (
            "🎉 *Analysis Complete!*\n\n"
            f"🚀 *Launch Frame Found:* {session.found_frame:,}\n"
            f"📊 *Total Steps:* {session.steps_taken}\n"
            f"🎯 *Total Frames Analyzed:* {session.total_frames:,}\n\n"
            "📸 *Note:* The launch frame image could not be loaded, "
            "but the frame number above is correct!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Start Over", callback_data="restart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.callback_query.edit_message_text(
                result_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as edit_error:
            logger.error(f"Error editing results message: {edit_error}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=result_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def handle_restart(update: Update, context: CallbackContext):
    """Handle restart request"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    
    try:
        # End current session
        session_manager.end_session(user_id)
        logger.info(f"Session restarted for user {user_id}")
        
        # Get video info for new session
        video_info = frame_client.get_video_info(Config.VIDEO_NAME)
        
        # Create new user session - FIXED: use user_id instead of user.id
        session = session_manager.create_session(user_id, video_info.frames)  # FIXED LINE
        progress = session.get_progress_info()

        # Send new welcome message with clearer instructions
        welcome_text = (
            "🔄 *Session Restarted!*\n\n"
            "🚀 *Rocket Launch Frame Detector*\n\n"
            "I'll help you find the exact frame where the Falcon Heavy rocket LAUNCHES!\n"
            f"• Total frames: {video_info.frames:,}\n"
            f"• Estimated steps: {progress['remaining_steps'] + progress['steps_taken']}\n\n"
            "🔴 *CRITICAL: What to look for:*\n"
            "• ❌ NO: SpaceX studio, hosts talking, countdown, static rocket on pad\n"
            "• ❌ NO: Tesla Roadster in space (this happens AFTER launch)\n"
            "• ✅ YES: ONLY when you see FIRE/SMOKE and the rocket MOVING UPWARD from the launch pad"
        )

        try:
            # First try to edit the caption if it's a photo message
            await query.edit_message_caption(
                caption=welcome_text,
                parse_mode='Markdown'
            )
        except BadRequest:
            # If that fails (message is text, not photo), edit as text
            await query.edit_message_text(
                welcome_text,
                parse_mode='Markdown'
            )
        
        # Show first frame
        await show_current_frame(update, context, session)
        
    except Exception as e:
        logger.error(f"Error during restart for user {user_id}: {e}", exc_info=True)
        error_msg = "❌ Error restarting session. Please try /start"
        try:
            # Try multiple approaches to ensure we can send the error message
            try:
                await query.edit_message_text(error_msg)
            except BadRequest:
                await query.edit_message_caption(caption=error_msg)
        except Exception as edit_error:
            logger.error(f"Error editing message during restart: {edit_error}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=error_msg
            )
            
async def handle_session_expired(update: Update, context: CallbackContext):
    """Handle expired session"""
    error_msg = "❌ Session expired or not found. Please start again with /start"
    if update.callback_query:
        await update.callback_query.edit_message_text(error_msg)
    else:
        await update.message.reply_text(error_msg)