import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant

# ==========================================
# ENVIRONMENT VARIABLES
# ==========================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "@Allutvserials")
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "Anujith1238")
# ==========================================

app = Client("rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}          
user_tasks = {}         
user_renaming = {}      
waiting_for_thumb = {}  

# ഫോഴ്സ് സബ്‌സ്‌ക്രൈബ് പരിശോധനയ്ക്കുള്ള ഫങ്ഷൻ
async def check_force_sub(client, user_id):
    if user_id == ADMIN_USER_ID:
        return True
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if user.status in ["banned", "left"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True  

# /start കമാൻഡ്
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    
    is_subbed = await check_force_sub(client, user_id)
    if not is_subbed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ])
        await message.reply_text(
            "⚠️ **Welcome to File Rename Bot!**\n\n"
            "To use this bot, you must subscribe to our channel first.",
            reply_markup=keyboard
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT}")]
    ])
    
    await message.reply_text(
        f"Hello {message.from_user.first_name}!\n\n"
        "I am an advanced file renaming bot. I can rename files, convert documents/videos, and manage custom thumbnails.\n\n"
        "Send me a file to get started!",
        reply_markup=keyboard
    )

# സബ്സ്ക്രൈബ് ചെക്ക് കോൾബാക്ക്
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_subbed = await check_force_sub(client, user_id)
    if is_subbed:
        await callback_query.message.delete()
        await callback_query.message.reply_text("✅ Thank you! Now you can send files.")
    else:
        await callback_query.answer("⚠️ You haven't joined the channel yet!", show_alert=True)

# /settings കമാൻഡ്
@app.on_message(filters.command("settings"))
async def settings_handler(client, message: Message):
    user_id = message.from_user.id
    thumb = user_data.get(user_id, {}).get("thumb")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Set Thumbnail", callback_data="set_thumb")],
        [InlineKeyboardButton("❌ Remove Thumbnail", callback_data="del_thumb")],
        [InlineKeyboardButton("🖼️ View Thumbnail", callback_data="view_thumb")]
    ])
    
    await message.reply_text(
        "🛠️ **Bot Settings**\n\n"
        f"Custom Thumbnail: {'Set ✅' if thumb else 'Not Set ❌'}",
        reply_markup=keyboard
    )

# സ്ലാഷ് കമാൻഡുകൾ
@app.on_message(filters.command("set_thumb"))
async def slash_set_thumb(client, message: Message):
    waiting_for_thumb[message.from_user.id] = True
    await message.reply_text("📷 Please send the photo you want to set as your custom thumbnail.")

@app.on_message(filters.command("del_thumb"))
async def slash_del_thumb(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id].get("thumb"):
        user_data[user_id]["thumb"] = None
        await message.reply_text("✅ Thumbnail successfully removed!")
    else:
        await message.reply_text("⚠️ No custom thumbnail found to remove.")

@app.on_message(filters.command("view_thumb"))
async def slash_view_thumb(client, message: Message):
    user_id = message.from_user.id
    thumb = user_data.get(user_id, {}).get("thumb")
    if thumb:
        await message.reply_photo(thumb, caption="Here is your current custom thumbnail.")
    else:
        await message.reply_text("⚠️ You haven't set any custom thumbnail yet.")

# ഇൻലൈൻ ബട്ടണുകൾ ഹാൻഡ്ലർ ചെയ്യൽ
@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "set_thumb":
        waiting_for_thumb[user_id] = True
        await callback_query.message.reply_text("📷 Please send the photo you want to set as your custom thumbnail.")
        await callback_query.answer()
        
    elif data == "view_thumb":
        thumb = user_data.get(user_id, {}).get("thumb")
        if thumb:
            await callback_query.message.reply_photo(thumb, caption="Here is your current custom thumbnail.")
        else:
            await callback_query.answer("No thumbnail found!", show_alert=True)
        await callback_query.answer()
            
    elif data == "del_thumb":
        if user_id in user_data and user_data[user_id].get("thumb"):
            user_data[user_id]["thumb"] = None
            await callback_query.answer("Thumbnail removed successfully!", show_alert=True)
        else:
            await callback_query.answer("No thumbnail to remove!", show_alert=True)
        await callback_query.answer()

# യൂസർ തംബ്‌നെയിലിനായി ഫോട്ടോ അയക്കുമ്പോൾ
@app.on_message(filters.photo & ~filters.command(["start", "settings"]))
async def save_thumbnail_photo(client, message: Message):
    user_id = message.from_user.id
    if waiting_for_thumb.get(user_id):
        photo_id = message.photo.file_id
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["thumb"] = photo_id
        waiting_for_thumb[user_id] = False
        await message.reply_text("✅ Custom thumbnail successfully saved!")

# ഫയലുകൾ സ്വീകരിക്കുമ്പോൾ
@app.on_message(filters.document | filters.video)
async def get_file(client, message: Message):
    user_id = message.from_user.id
    
    if not await check_force_sub(client, user_id):
        await message.reply_text(f"⚠️ Please join our channel {FORCE_SUB_CHANNEL} before sending files!")
        return

    active_tasks = user_tasks.get(user_id, 0)
    if user_id != ADMIN_USER_ID and active_tasks >= 2:
        await message.reply_text("⚠️ You already have 2 active tasks running. Please wait for them to complete!")
        return

    file_name = message.document.file_name if message.document else message.video.file_name
    user_renaming[user_id] = {
        "message": message,
        "file_name": file_name
    }
    
    await message.reply_text(
        f"📁 **Old File Name:** `{file_name}`\n\n"
        "Please send the new file name:\n"
        "*(Note: You can also use `-t <image_url>` to set a thumbnail on the fly)*"
    )

# പുതിയ ഫയൽ നെയിമും -t യുആർഎലും സ്വീകരിക്കുമ്പോൾ
@app.on_message(filters.text & ~filters.command(["start", "settings", "set_thumb", "del_thumb", "view_thumb"]))
async def rename_process(client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_renaming:
        return
        
    text = message.text.strip()
    custom_thumb_url = None
    
    if " -t " in text:
        parts = text.split(" -t ")
        new_name = parts[0].strip()
        custom_thumb_url = parts[1].strip()
    else:
        new_name = text

    old_file_name = user_renaming[user_id]["file_name"]
    ext = os.path.splitext(old_file_name)[1]
    if not new_name.endswith(ext):
        new_name += ext

    user_renaming[user_id]["new_name"] = new_name
    
    if custom_thumb_url:
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["temp_thumb_url"] = custom_thumb_url

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Document File", callback_data="format_doc"),
            InlineKeyboardButton("🎬 Video File", callback_data="format_vid")
        ]
    ])
    
    await message.reply_text(
        f"📂 **Select Output Format**\n\nFile Name :- `{new_name}`",
        reply_markup=keyboard
    )

# ഔട്ട്പുട്ട് ഫോർമാറ്റ് സെലക്ഷൻ ഹാൻഡ്ലർ
@app.on_callback_query(filters.regex("^format_"))
async def format_selection(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if user_id not in user_renaming:
        await callback_query.answer("Session expired. Please send the file again.", show_alert=True)
        return

    file_info = user_renaming[user_id]
    original_msg = file_info["message"]
    new_name = file_info["new_name"]
    
    user_tasks[user_id] = user_tasks.get(user_id, 0) + 1
    status_msg = await callback_query.message.edit_text("⏳ Downloading file...")
    
    file_path = None
    thumb_path = None
    
    try:
        file_path = await original_msg.download(file_name=new_name)
        
        thumb_url = user_data.get(user_id, {}).get("temp_thumb_url")
        saved_thumb = user_data.get(user_id, {}).get("thumb")
        
        if thumb_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumb_url) as resp:
                    if resp.status == 200:
                        thumb_path = f"thumb_{user_id}.jpg"
                        with open(thumb_path, "wb") as f:
                            f.write(await resp.read())
        elif saved_thumb and not isinstance(saved_thumb, str): 
            thumb_path = await client.download_media(saved_thumb, file_name=f"thumb_{user_id}.jpg")

        await status_msg.edit_text("📤 Uploading file...")
        
        if data == "format_doc":
            await client.send_document(
                chat_id=callback_query.message.chat.id,
                document=file_path,
                thumb=thumb_path,
                caption=f"`{new_name}`"
            )
        else:
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=file_path,
                thumb=thumb_path,
                caption=f"`{new_name}`"
            )
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred: `{e}`")
        
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        user_tasks[user_id] = max(0, user_tasks.get(user_id, 1) - 1)
        if user_id in user_renaming:
            del user_renaming[user_id]

print("Bot is up and running successfully!")
app.run()
