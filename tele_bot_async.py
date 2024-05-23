import logging

from telegram import ForceReply, Update 
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from dotenv import dotenv_values
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from utils import *

# Load environment variables as a dictionary
env_vars = dotenv_values("secret.env")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define single states for add and remove conversations
ADDING = 1
REMOVE = 1

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    #print(f"effective_user: {update.effective_user.id}")
    logger.info(f"effective_chat used `/start` command: {update.effective_chat.id}")
    #print(f"effective_sender: {update.effective_sender.id}")
    
    chat = update.effective_chat
    
    await update.message.reply_text("""
                                    Welcome to FollowSleuth, your personalised tracker for mainly Web3 focused KOLs/profiles on X (Formerly Twitter).
                                    \nThis is currently in early development stages and an one man show pet project.
                                    \nApologies if there are bugs, let me know if there is any issues via Discord.
                                    \nUpdates will be pushed on regularly on a 30 mins basis.
                                    \nPress /help to get more info on how to utilise the bot :)
                                    """)
    context.user_data.clear()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"effective_chat used `/help` command: {update.effective_chat.id}")
    await update.message.reply_text("""
                                    /register : add your chat to database for push updates
                                    \n/add_handle : add one or more handles to database for tracking
                                    \n/show_handles: show your current list of handles you are tracking
                                    \n/remove_handle : remove an existing handle from database for tracking
                                    \n/abort : cancel out any add_handle or remove_handle commands made
                                    \n/stop : stop tracking updates being pushed to chat (handles tracking list remains intact)
                                    \n/resume: resume tracking updates
                                    \n/destruct: remove your account and tracking list from database completely
                                    """)
    context.user_data.clear()


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /register is issued."""
    logger.info(f"effective_chat used `/register` command: {update.effective_chat.id}")
    
    existing = existing_chat(chat_id=update.effective_chat.id)
    if existing:
        await update.message.reply_text("🙂 You have already registered! 🙂")
    else:
        register =  register_chat(update.effective_chat.id)
        if register:
            await update.message.reply_text("🙌 Successfully registered! 🙌")
        else:
            await update.message.reply_text("❌ Error in registering! ❌")
    context.user_data.clear()


async def add_handles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /add_handle is issued."""
    logger.info(f"effective_chat used `/add_handle` command: {update.effective_chat.id}")
    
    existing = existing_chat(update.effective_chat.id)
    if existing:
        await update.message.reply_text("Please enter the handle you wish to track, exclude '@' symbol\
                                        and use newlines if multiple handles", reply_markup=ForceReply(selective=True))
        return ADDING
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
        return ConversationHandler.END

async def received_adding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when user replies after command /add_handle is issued."""
    user_input = update.message.text
    await update.message.reply_text(f"Handles Added:\n{user_input}")
    add = add_handles_to_db(user_input=user_input, chat_id=update.effective_chat.id)
    if add:
        await update.message.reply_text("🙌 Successfully added handles! 🙌")
    else:
        await update.message.reply_text("❌ Error in adding handles! ❌")
    context.user_data.clear()
    return ConversationHandler.END


async def remove_handles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /remove_handles is issued."""
    logger.info(f"effective_chat used `/add_handle` command: {update.effective_chat.id}")
    
    existing = existing_chat(update.effective_chat.id)
    if existing:
        await update.message.reply_text("Please enter the handle you wish to remove, exclude '@' symbol\
                                        and use newlines if multiple handles", reply_markup=ForceReply(selective=True))
        return REMOVE
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
        return ConversationHandler.END


async def received_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when user replies after command /remove_handles is issued."""
    user_input = update.message.text
    await update.message.reply_text(f"Handles Removed:\
                                    {user_input}")
    add = remove_handles_from_db(user_input=user_input, chat_id=update.effective_chat.id)
    if add:
        await update.message.reply_text("🙌 Successfully removed handles! 🙌")
    else:
        await update.message.reply_text("❌ Error in removing handles! ❌")
    context.user_data.clear()
    return ConversationHandler.END


async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /show_handles is issued."""
    logger.info(f"effective_chat used `/show_handles` command: {update.effective_chat.id}")
    
    existing = existing_chat(chat_id=update.effective_chat.id)
    if existing:
        current_list = retrieve_handles_from_db(chat_id=update.effective_chat.id)
        await update.message.reply_text(f"📜 Here's your current list of handles 📜\n{current_list}")
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
    context.user_data.clear()


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /stop is issued."""
    logger.info(f"effective_chat used `/stop` command: {update.effective_chat.id}")
    
    existing = existing_chat(chat_id=update.effective_chat.id)
    if existing:
        stop_status = stop_tracking(chat_id=update.effective_chat.id)
        if stop_status:
            await update.message.reply_text("🛑 Tracking has been stopped 🛑")
        else:
            await update.message.reply_text("❌ Error in halting tracking! ❌")
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
    context.user_data.clear()


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /resume is issued."""
    logger.info(f"effective_chat used `/resume` command: {update.effective_chat.id}")
    
    existing = existing_chat(chat_id=update.effective_chat.id)
    if existing:
        resume_status = resume_tracking(chat_id=update.effective_chat.id)
        if resume_status:
            await update.message.reply_text("🟢 Tracking has been resumed 🟢")
        else:
            await update.message.reply_text("❌ Error in resuming tracking! ❌")
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
    context.user_data.clear()


async def destruct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /destruct is issued."""
    logger.info(f"effective_chat used `/destruct` command: {update.effective_chat.id}")
    
    existing = existing_chat(chat_id=update.effective_chat.id)
    if existing:
        destruct_status = self_destruct(chat_id=update.effective_chat.id)
        if destruct_status:
            await update.message.reply_text("💣💥Tracking list and account removed!💥💣")
        else:
            await update.message.reply_text("❌ Error in destructing! ❌")
    else:
        await update.message.reply_text("❌ You are not registered! ❌")
    context.user_data.clear()


async def abort(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("The operation has been cancelled.")
    return ConversationHandler.END


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    context.user_data.clear()
    await update.message.reply_text("🚫 Unrecognised command! 🚫")



# Initialize python telegram bot
ptb = (
    Application.builder()
    .updater(None)
    .token(env_vars['bot_token']) # replace <your-bot-token>
    .read_timeout(7)
    .get_updates_read_timeout(42)
    .build()
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await ptb.bot.setWebhook("") # replace <your-webhook-url>
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()

# Initialize FastAPI app (similar to Flask)
app = FastAPI(lifespan=lifespan)

@app.post("/")
async def process_update(request: Request):
    req = await request.json()
    update = Update.de_json(req, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)


# on different commands - answer in Telegram
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("help", help_command))
ptb.add_handler(CommandHandler("register", register_command))

add_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('add_handle', add_handles)],
    states={
        ADDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_adding)],
    },
    fallbacks=[CommandHandler('abort', abort)],
)
ptb.add_handler(add_conv_handler)

remove_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('remove_handle', remove_handles)],
    states={
        REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_remove)],
    },
    fallbacks=[CommandHandler('abort', abort)],
)
ptb.add_handler(remove_conv_handler)

ptb.add_handler(CommandHandler("show_handles", show_command))
ptb.add_handler(CommandHandler("stop", stop_command))
ptb.add_handler(CommandHandler("resume", resume_command))
ptb.add_handler(CommandHandler("destruct", destruct_command))

# on non commands - echo the message on Telegram
ptb.add_handler(MessageHandler(~filters.COMMAND, echo))



