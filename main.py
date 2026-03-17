# -*- coding: utf-8 -*-
"""
ULTIMATE OWNER BOT - Perfect Working Version
By @CyberHacked0 - Exclusive for Owner: 8062814840
"""

import telebot
import subprocess
import os
import shutil
from telebot import types
import time
from datetime import datetime
import sqlite3
import json
import logging
import threading
import sys
import atexit

# --- CONFIGURATION ---
TOKEN = '8573908079:AAGEgavNXWZ4dpKdmvedwcW4x8SEsBuGQrs'
OWNER_ID = 6357008488
ADMIN_IDS = set()

# Folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'owner_scripts')
LOGS_DIR = os.path.join(BASE_DIR, 'execution_logs')
DATABASE_PATH = os.path.join(BASE_DIR, 'owner_bot.db')

# Create directories
for directory in [UPLOAD_BOTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Data structures
bot_scripts = {}
user_files = {}
admin_ids = set()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Command buttons
OWNER_COMMANDS = [
    ["🚀 Upload Script", "📂 My Scripts"],
    ["🟢 Running Scripts", "📊 Stats"],
    ["👥 Manage Admins", "📢 Broadcast"],
    ["🛠️ Utilities", "❓ Help"]
]

# Database functions
def init_db():
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY, username TEXT, added_by INTEGER, added_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS running_scripts
                     (user_id INTEGER, file_name TEXT, start_time TEXT, pid INTEGER,
                      PRIMARY KEY (user_id, file_name))''')

        # Add owner
        c.execute('INSERT OR IGNORE INTO admins (user_id, username, added_by, added_date) VALUES (?, ?, ?, ?)',
                 (OWNER_ID, 'Owner', OWNER_ID, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database error: {e}")

def load_data():
    global admin_ids, user_files
    
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        # Load admins
        c.execute('SELECT user_id FROM admins')
        admin_ids = set(user_id for (user_id,) in c.fetchall())

        # Load user files
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))

        conn.close()
        logger.info(f"Data loaded: {len(admin_ids)} admins")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def add_admin(user_id, username, added_by):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO admins (user_id, username, added_by, added_date) VALUES (?, ?, ?, ?)',
                 (user_id, username, added_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        admin_ids.add(user_id)
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False

def remove_admin(user_id):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        if user_id in admin_ids:
            admin_ids.remove(user_id)
        return True
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return False

def get_admins():
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, username FROM admins')
        admins = c.fetchall()
        conn.close()
        return admins
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return []

def save_user_file(user_id, file_name, file_type):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_time) VALUES (?, ?, ?, ?)',
                 (user_id, file_name, file_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving file: {e}")

def remove_user_file(user_id, file_name):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error removing file: {e}")

def save_running_script(user_id, file_name, pid=None):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO running_scripts (user_id, file_name, start_time, pid) VALUES (?, ?, ?, ?)',
                 (user_id, file_name, datetime.now().isoformat(), pid))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving running script: {e}")

def remove_running_script(user_id, file_name):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM running_scripts WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error removing running script: {e}")

# Helper functions
def get_user_folder(user_id):
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(user_id, file_name):
    script_key = f"{user_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            return script_info['process'].poll() is None
        except:
            return False
    return False

def get_script_uptime(user_id, file_name):
    script_key = f"{user_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('start_time'):
        uptime = datetime.now() - script_info['start_time']
        return str(uptime).split('.')[0]
    return None

def safe_send_message(chat_id, text, reply_markup=None):
    try:
        return bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return None

def safe_reply_to(message, text, reply_markup=None):
    try:
        return bot.reply_to(message, text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Reply error: {e}")
        return None

def safe_edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        return bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Edit message error: {e}")
        return None

# Script execution
def execute_script(user_id, script_path, message_for_updates=None):
    script_name = os.path.basename(script_path)
    script_ext = os.path.splitext(script_path)[1].lower()

    supported_types = {
        '.py': {'name': 'Python', 'icon': '🐍', 'executable': True},
        '.js': {'name': 'JavaScript', 'icon': '🟨', 'executable': True},
        '.sh': {'name': 'Shell', 'icon': '🖥️', 'executable': True},
        '.txt': {'name': 'Text', 'icon': '📄', 'executable': False},
        '.zip': {'name': 'ZIP', 'icon': '📦', 'executable': False},
        '.html': {'name': 'HTML', 'icon': '🌐', 'executable': False},
        '.css': {'name': 'CSS', 'icon': '🎨', 'executable': False},
    }

    if script_ext not in supported_types:
        return False, f"Unsupported file type: {script_ext}"

    lang_info = supported_types[script_ext]

    try:
        if message_for_updates:
            safe_edit_message(
                message_for_updates.chat.id,
                message_for_updates.message_id,
                f"🚀 Starting {script_name}..."
            )

        if not lang_info.get('executable', True):
            return True, "File stored successfully"

        if script_ext == '.py':
            cmd = [sys.executable, script_path]
        elif script_ext == '.js':
            cmd = ['node', script_path]
        elif script_ext == '.sh':
            cmd = ['bash', script_path]
        else:
            cmd = [script_path]

        log_file_path = os.path.join(LOGS_DIR, f"{user_id}_{int(time.time())}.log")

        with open(log_file_path, 'w') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(script_path),
                env=os.environ.copy()
            )

            script_key = f"{user_id}_{script_name}"
            bot_scripts[script_key] = {
                'process': process,
                'user_id': user_id,
                'file_name': script_name,
                'start_time': datetime.now(),
                'log_file_path': log_file_path,
                'language': lang_info['name'],
                'icon': lang_info['icon']
            }

            save_running_script(user_id, script_name, process.pid)

            if message_for_updates:
                success_msg = f"✅ {script_name} started!\n\n"
                success_msg += f"🔧 Language: {lang_info['name']}\n"
                success_msg += f"🆔 PID: {process.pid}\n"
                success_msg += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n"
                success_msg += f"📊 Status: 🟢 Running"

                safe_edit_message(
                    message_for_updates.chat.id, 
                    message_for_updates.message_id, 
                    success_msg
                )

            return True, f"Script started with PID {process.pid}"

    except Exception as e:
        error_msg = f"Execution failed: {str(e)}"
        logger.error(f"Script execution error: {e}")

        if message_for_updates:
            safe_edit_message(
                message_for_updates.chat.id, 
                message_for_updates.message_id, 
                f"❌ {error_msg}"
            )

        return False, error_msg

# Command handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED\n\nThis is a private owner bot.")
        return

    welcome_msg = f"🔐 OWNER BOT - Advanced Script Hosting\n\n"
    welcome_msg += f"👋 Welcome {message.from_user.first_name}!\n\n"
    
    if user_id == OWNER_ID:
        welcome_msg += f"👑 Status: OWNER (Full Access)\n"
    else:
        welcome_msg += f"🔧 Status: ADMIN\n"
        
    welcome_msg += f"📁 Your Files: {get_user_file_count(user_id)}\n"
    welcome_msg += f"🚀 Running Scripts: {len([s for s in bot_scripts.values() if s['user_id'] == user_id])}\n\n"
    welcome_msg += f"💡 Use the menu below to get started!"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in OWNER_COMMANDS:
        markup.add(*[types.KeyboardButton(text) for text in row])

    safe_send_message(message.chat.id, welcome_msg, reply_markup=markup)
    logger.info(f"User {user_id} started bot")

@bot.message_handler(content_types=['document'])
def handle_file_upload(message):
    user_id = message.from_user.id

    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED\n\nAdmin privileges required!")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name or f"file_{int(time.time())}"
        
        processing_msg = safe_reply_to(message, f"📥 Downloading {file_name}...")

        downloaded_file = bot.download_file(file_info.file_path)

        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)

        file_ext = os.path.splitext(file_name)[1].lower()
        file_type = 'executable' if file_ext in {'.py', '.js', '.sh'} else 'hosted'

        if user_id not in user_files:
            user_files[user_id] = []

        user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
        user_files[user_id].append((file_name, file_type))

        save_user_file(user_id, file_name, file_type)

        success_msg = f"✅ {file_name} uploaded successfully!\n\n"
        success_msg += f"📁 Type: {file_type}\n"
        success_msg += f"💾 Size: {message.document.file_size} bytes\n"
        
        if file_type == 'executable':
            success_msg += f"🚀 Ready for execution\n"
            success_msg += f"💡 Use 'My Scripts' to run it"
        else:
            success_msg += f"📦 Securely stored\n"

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, success_msg)

        logger.info(f"File uploaded by {user_id}: {file_name}")

    except Exception as e:
        logger.error(f"File upload error: {e}")
        safe_reply_to(message, f"❌ Upload failed: {str(e)}")

# Button handlers
@bot.message_handler(func=lambda message: message.text == "🚀 Upload Script")
def upload_script_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return
        
    safe_reply_to(message, 
                 "📤 Upload Any Script/File\n\n"
                 "🚀 Supported Executables:\n"
                 "🐍 Python (.py) files\n"
                 "🟨 JavaScript (.js) files\n" 
                 "🖥️ Shell (.sh) scripts\n\n"
                 "📁 Supported Storage:\n"
                 "📦 ZIP Archives\n"
                 "🌐 HTML/CSS files\n"
                 "📄 Text files\n\n"
                 "💡 Just send me the file!")

@bot.message_handler(func=lambda message: message.text == "📂 My Scripts")
def my_scripts_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED @CyberHacked0")
        return
        
    files = user_files.get(user_id, [])

    if not files:
        safe_reply_to(message, "📂 Your Scripts\n\nNo files uploaded yet.\n\n💡 Upload any file to begin!")
        return

    files_text = f"📂 Your Scripts ({len(files)} files)\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)

    for file_name, file_type in files:
        if file_type == 'executable':
            is_running = is_bot_running(user_id, file_name)
            status = "🟢 Running" if is_running else "⭕ Stopped"
            icon = "🚀"
            
            if is_running:
                uptime = get_script_uptime(user_id, file_name)
                if uptime:
                    status += f" ({uptime})"
        else:
            status = "📁 Stored"
            icon = "📄"

        files_text += f"{icon} {file_name}\nStatus: {status}\n\n"

        markup.add(types.InlineKeyboardButton(
            f"{icon} {file_name} - {status}", 
            callback_data=f'control_{user_id}_{file_name}'
        ))

    safe_reply_to(message, files_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🟢 Running Scripts")
def running_scripts_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    user_scripts = [s for s in bot_scripts.values() if s['user_id'] == user_id]

    if not user_scripts:
        safe_reply_to(message, "🟢 Running Scripts\n\nNo scripts currently running.")
        return

    running_text = f"🟢 Your Running Scripts\n\n"

    for script in user_scripts:
        uptime = get_script_uptime(script['user_id'], script['file_name']) or "Unknown"
        running_text += f"{script['icon']} {script['file_name']}\n"
        running_text += f"🔧 {script['language']}\n"
        running_text += f"⏱️ Uptime: {uptime}\n"
        running_text += f"🆔 PID: {script['process'].pid}\n\n"

    safe_reply_to(message, running_text)

@bot.message_handler(func=lambda message: message.text == "📊 Stats")
def stats_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    total_files = sum(len(files) for files in user_files.values())
    running_scripts = len(bot_scripts)

    stats_text = f"📊 Bot Statistics\n\n"
    stats_text += f"👥 Total Admins: {len(admin_ids)}\n"
    stats_text += f"📁 Total Files: {total_files}\n"
    stats_text += f"🚀 Running Scripts: {running_scripts}\n"
    stats_text += f"👤 Your Files: {get_user_file_count(user_id)}\n"

    safe_reply_to(message, stats_text)

@bot.message_handler(func=lambda message: message.text == "👥 Manage Admins")
def manage_admins_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        safe_reply_to(message, "🚫 Owner Only\n\nOnly the owner can manage admins.")
        return

    admins = get_admins()
    
    admin_text = f"👥 Admin Management\n\n"
    admin_text += f"Total Admins: {len(admins)}\n\n"
    
    for admin_id, username in admins:
        role = "👑 OWNER @CyberHacked0" if admin_id == OWNER_ID else "🔧 ADMIN"
        admin_text += f"{role} - {admin_id}\n"
        if username and username != "Unknown":
            admin_text += f"   @{username}\n"
        admin_text += f"\n"

    admin_text += "🔧 Commands:\n"
    admin_text += "• /addadmin <user_id> <username> - Add admin\n"
    admin_text += "• /removeadmin <user_id> - Remove admin\n"
    admin_text += "• /listadmins - Show all admins"

    safe_reply_to(message, admin_text)

@bot.message_handler(func=lambda message: message.text == "📢 Broadcast")
def broadcast_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    msg = safe_reply_to(message, 
                       "📢 BROADCAST MESSAGE\n\n"
                       "💬 Send the message you want to broadcast to all admins.\n"
                       "❌ Send /cancel to cancel.")
    
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    user_id = message.from_user.id
    
    if message.text == '/cancel':
        safe_reply_to(message, "❌ Broadcast cancelled.")
        return
        
    broadcast_content = message.text
    success_count = 0
    failed_count = 0
    
    processing_msg = safe_reply_to(message, f"📤 Broadcasting to {len(admin_ids)} admins...")
    
    for admin_id in admin_ids:
        try:
            if admin_id != user_id:  # Don't send to self
                bot.send_message(admin_id, f"📢 Broadcast Message\n\n{broadcast_content}\n\n- From Admin {user_id}")
                success_count += 1
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send broadcast to {admin_id}: {e}")
            failed_count += 1
    
    result_msg = f"📊 Broadcast Complete\n\n"
    result_msg += f"✅ Success: {success_count}\n"
    result_msg += f"❌ Failed: {failed_count}\n"
    result_msg += f"📨 Total: {len(admin_ids)} admins"
    
    safe_edit_message(processing_msg.chat.id, processing_msg.message_id, result_msg)

@bot.message_handler(func=lambda message: message.text == "🛠️ Utilities")
def utilities_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    utilities_text = f"🛠️ Owner Bot Utilities\n\n"
    utilities_text += f"🔧 Available Commands:\n\n"
    utilities_text += f"• /restart <filename> - Restart a script\n"
    utilities_text += f"• /stop <filename> - Stop a running script\n"
    utilities_text += f"• /logs <filename> - Get live logs of a script\n"
    utilities_text += f"• /cleanup - Remove all stopped scripts\n\n"
    utilities_text += f"💡 Use these commands for advanced management!"

    safe_reply_to(message, utilities_text)

@bot.message_handler(func=lambda message: message.text == "❓ Help")
def help_button(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    help_text = f"❓ Owner Bot Help\n\n"
    help_text += "🔐 ACCESS CONTROL:\n"
    help_text += "• Only owner and added admins can use\n"
    help_text += "• Owner can add/remove admins\n\n"
    help_text += "🚀 SCRIPT HOSTING:\n"
    help_text += "• Upload Python, JavaScript, Shell scripts\n"
    help_text += "• Start/Stop/Restart scripts\n"
    help_text += "• View real-time execution logs\n\n"
    help_text += "📁 FILE STORAGE:\n"
    help_text += "• Store any file type\n"
    help_text += "• ZIP, HTML, CSS, Text files\n\n"
    help_text += "💡 Use menu buttons for all features!"

    safe_reply_to(message, help_text)

# Admin commands
@bot.message_handler(commands=['addadmin'])
def add_admin_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        safe_reply_to(message, "🚫 Owner Only\n\nOnly the owner can add admins.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            safe_reply_to(message, "❌ Usage: /addadmin <user_id> [username]")
            return

        target_user_id = int(parts[1])
        username = parts[2] if len(parts) > 2 else "Unknown"
        
        if add_admin(target_user_id, username, user_id):
            safe_reply_to(message, f"✅ Admin added successfully!\n\nUser ID: {target_user_id}\nUsername: {username}")
        else:
            safe_reply_to(message, "❌ Failed to add admin!")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        safe_reply_to(message, "🚫 Owner Only\n\nOnly the owner can remove admins.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /removeadmin <user_id>")
            return

        target_user_id = int(parts[1])
        
        if target_user_id == OWNER_ID:
            safe_reply_to(message, "❌ Cannot remove owner!")
            return
            
        if remove_admin(target_user_id):
            safe_reply_to(message, f"✅ Admin removed successfully!\n\nUser ID: {target_user_id}")
        else:
            safe_reply_to(message, "❌ Failed to remove admin!")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['listadmins'])
def list_admins_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    admins = get_admins()
    
    admin_text = f"👥 Admin List\n\n"
    admin_text += f"Total: {len(admins)}\n\n"
    
    for admin_id, username in admins:
        role = "👑 OWNER" if admin_id == OWNER_ID else "🔧 ADMIN"
        admin_text += f"{role}\n"
        admin_text += f"ID: {admin_id}\n"
        if username and username != "Unknown":
            admin_text += f"Username: @{username}\n"
        admin_text += f"\n"

    safe_reply_to(message, admin_text)

# Utility commands
@bot.message_handler(commands=['restart'])
def restart_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /restart <filename>")
            return

        file_name = parts[1]
        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        if not os.path.exists(file_path):
            safe_reply_to(message, f"❌ File not found: {file_name}")
            return

        # Stop if running
        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            try:
                process = bot_scripts[script_key]['process']
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
            except:
                pass

        # Start again
        success, result = execute_script(user_id, file_path)
        
        if success:
            safe_reply_to(message, f"🔄 Script restarted successfully!\n\nFile: {file_name}")
        else:
            safe_reply_to(message, f"❌ Restart failed: {result}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /stop <filename>")
            return

        file_name = parts[1]
        script_key = f"{user_id}_{file_name}"
        
        if script_key in bot_scripts:
            try:
                process = bot_scripts[script_key]['process']
                runtime = get_script_uptime(user_id, file_name) or "Unknown"
                
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
                
                safe_reply_to(message, f"🔴 Script stopped!\n\nFile: {file_name}\nRuntime: {runtime}")
            except Exception as e:
                safe_reply_to(message, f"❌ Stop failed: {str(e)}")
        else:
            safe_reply_to(message, f"❌ Script not running: {file_name}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['logs'])
def logs_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /logs <filename>")
            return

        file_name = parts[1]
        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)
        
        if script_info and 'log_file_path' in script_info:
            log_file_path = script_info['log_file_path']
            
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r') as f:
                    logs = f.read()
                
                if logs.strip():
                    if len(logs) > 4000:
                        logs = "..." + logs[-4000:]
                    
                    logs_text = f"📜 Execution Logs - {file_name}\n\n```\n{logs}\n```"
                    safe_reply_to(message, logs_text, parse_mode='Markdown')
                else:
                    safe_reply_to(message, f"📜 Execution Logs - {file_name}\n\nNo output yet")
            else:
                safe_reply_to(message, f"❌ Log file not found for: {file_name}")
        else:
            safe_reply_to(message, f"❌ No logs available for: {file_name}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['cleanup'])
def cleanup_command(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_ids:
        safe_reply_to(message, "🚫 ACCESS DENIED")
        return

    stopped_count = 0
    for script_key in list(bot_scripts.keys()):
        script_info = bot_scripts[script_key]
        if not is_bot_running(script_info['user_id'], script_info['file_name']):
            remove_running_script(script_info['user_id'], script_info['file_name'])
            del bot_scripts[script_key]
            stopped_count += 1

    safe_reply_to(message, f"🧹 Cleanup completed!\n\nRemoved {stopped_count} stopped scripts from memory.")

# Inline button handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('control_'))
def handle_file_control(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        user_files_list = user_files.get(user_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        
        if not file_info:
            bot.answer_callback_query(call.id, "❌ File not found!")
            return
            
        file_name, file_type = file_info
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        if file_type == 'executable':
            is_running = is_bot_running(user_id, file_name)
            
            if is_running:
                markup.add(
                    types.InlineKeyboardButton("🔴 Stop", callback_data=f'stop_{user_id}_{file_name}'),
                    types.InlineKeyboardButton("🔄 Restart", callback_data=f'restart_{user_id}_{file_name}'),
                    types.InlineKeyboardButton("📜 Logs", callback_data=f'logs_{user_id}_{file_name}')
                )
            else:
                markup.add(
                    types.InlineKeyboardButton("🟢 Start", callback_data=f'start_{user_id}_{file_name}'),
                    types.InlineKeyboardButton("📜 Logs", callback_data=f'logs_{user_id}_{file_name}')
                )
        
        markup.add(
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f'delete_{user_id}_{file_name}'),
            types.InlineKeyboardButton("🔙 Back", callback_data=f'back_{user_id}')
        )
        
        status = "🟢 Running" if file_type == 'executable' and is_bot_running(user_id, file_name) else "⭕ Stopped" if file_type == 'executable' else "📁 Stored"
        
        control_text = f"🔧 File Control Panel\n\n"
        control_text += f"📄 File: {file_name}\n"
        control_text += f"📁 Type: {file_type}\n"
        control_text += f"🔄 Status: {status}\n"
        
        if file_type == 'executable' and is_running:
            uptime = get_script_uptime(user_id, file_name)
            if uptime:
                control_text += f"⏱️ Uptime: {uptime}\n"
        
        control_text += f"👤 Owner: {user_id}\n\n"
        control_text += f"🎛️ Choose an action:"
        
        bot.edit_message_text(
            control_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
        bot.answer_callback_query(call.id, f"Control panel for {file_name}")
        
    except Exception as e:
        logger.error(f"Error in file control handler: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def handle_start_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ File not found!")
            return
            
        if is_bot_running(user_id, file_name):
            bot.answer_callback_query(call.id, "⚠️ Already running!")
            return
            
        success, result = execute_script(user_id, file_path, call.message)
        
        if success:
            bot.answer_callback_query(call.id, "🟢 Started successfully!")
            call.data = f'control_{user_id}_{file_name}'
            handle_file_control(call)
        else:
            bot.answer_callback_query(call.id, f"❌ Start failed: {result}")
            
    except Exception as e:
        logger.error(f"Error starting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def handle_stop_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)
        
        if script_info and script_info.get('process'):
            try:
                runtime = get_script_uptime(user_id, file_name) or "Unknown"
                
                process = script_info['process']
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
                
                bot.answer_callback_query(call.id, f"🔴 Stopped! Runtime: {runtime}")
                call.data = f'control_{user_id}_{file_name}'
                handle_file_control(call)
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Stop failed: {str(e)}")
        else:
            bot.answer_callback_query(call.id, "⚠️ Not running!")
            
    except Exception as e:
        logger.error(f"Error stopping file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('restart_'))
def handle_restart_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)
        
        if script_info and script_info.get('process'):
            try:
                process = script_info['process']
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
            except:
                pass
        
        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        if os.path.exists(file_path):
            success, result = execute_script(user_id, file_path, call.message)
            
            if success:
                bot.answer_callback_query(call.id, "🔄 Restarted successfully!")
                call.data = f'control_{user_id}_{file_name}'
                handle_file_control(call)
            else:
                bot.answer_callback_query(call.id, f"❌ Restart failed: {result}")
        else:
            bot.answer_callback_query(call.id, "❌ File not found!")
            
    except Exception as e:
        logger.error(f"Error restarting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('logs_'))
def handle_show_logs(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)
        
        if script_info and 'log_file_path' in script_info:
            log_file_path = script_info['log_file_path']
            
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r') as f:
                        logs = f.read()
                    
                    if logs.strip():
                        if len(logs) > 4000:
                            logs = "..." + logs[-4000:]
                        
                        logs_text = f"📜 Execution Logs - {file_name}\n\n```\n{logs}\n```"
                        bot.send_message(call.message.chat.id, logs_text, parse_mode='Markdown')
                        bot.answer_callback_query(call.id, "📜 Logs sent!")
                    else:
                        bot.answer_callback_query(call.id, "🔇 No output yet")
                    
                except Exception as e:
                    bot.answer_callback_query(call.id, f"❌ Error reading logs: {str(e)}")
            else:
                bot.answer_callback_query(call.id, "❌ Log file not found!")
        else:
            bot.answer_callback_query(call.id, "❌ No logs available!")
            
    except Exception as e:
        logger.error(f"Error showing logs: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]
        
        if call.from_user.id != user_id and call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return
            
        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            try:
                process = bot_scripts[script_key]['process']
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
            except:
                pass
        
        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if user_id in user_files:
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
        
        remove_user_file(user_id, file_name)
        
        bot.answer_callback_query(call.id, f"🗑️ {file_name} deleted!")
        
        call.data = f'back_{user_id}'
        handle_back_to_files(call)
        
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_'))
def handle_back_to_files(call):
    try:
        parts = call.data.split('_', 1)
        user_id = int(parts[1])
        
        files = user_files.get(user_id, [])
        
        if not files:
            files_text = "📂 Your Scripts\n\nNo files uploaded yet.\n\n💡 Upload any file to begin!"
            markup = None
        else:
            files_text = f"📂 Your Scripts ({len(files)} files)\n\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for file_name, file_type in files:
                if file_type == 'executable':
                    is_running = is_bot_running(user_id, file_name)
                    status = "🟢 Running" if is_running else "⭕ Stopped"
                    icon = "🚀"
                    
                    if is_running:
                        uptime = get_script_uptime(user_id, file_name)
                        if uptime:
                            status += f" ({uptime})"
                else:
                    status = "📁 Stored"
                    icon = "📄"
                
                files_text += f"{icon} {file_name}\nStatus: {status}\n\n"
                
                markup.add(types.InlineKeyboardButton(
                    f"{icon} {file_name} - {status}", 
                    callback_data=f'control_{user_id}_{file_name}'
                ))
        
        bot.edit_message_text(
            files_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
        bot.answer_callback_query(call.id, "📂 Files list updated!")
        
    except Exception as e:
        logger.error(f"Error going back to files: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

# Catch-all handler
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    safe_reply_to(message, "❓ Use the menu buttons or /start for help.")

# Startup
def send_startup_message():
    try:
        bot_info = bot.get_me()
        startup_msg = f"🚀 OWNER BOT STARTED\n\n"
        startup_msg += f"🤖 Bot: @{bot_info.username}\n"
        startup_msg += f"👑 Owner: {OWNER_ID}\n"
        startup_msg += f"👥 Admins: {len(admin_ids)}\n"
        startup_msg += f"📁 Files: {sum(len(files) for files in user_files.values())}\n"
        startup_msg += f"🚀 Scripts: {len(bot_scripts)}\n"
        startup_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        bot.send_message(OWNER_ID, startup_msg)
    except Exception as e:
        logger.error(f"Error sending startup message: {e}")

if __name__ == "__main__":
    init_db()
    load_data()
    
    logger.info("🚀 Starting ULTIMATE OWNER BOT...")
    
    try:
        bot_info = bot.get_me()
        logger.info(f"Bot connected: @{bot_info.username}")
        
        print(f"🤖 OWNER BOT STARTED!")
        print(f"👑 Owner ID: {OWNER_ID}")
        print(f"👥 Admins: {len(admin_ids)}")
        print(f"📁 Files: {sum(len(files) for files in user_files.values())}")
        print(f"🚀 Scripts: {len(bot_scripts)}")
        
        send_startup_message()
        
        bot.infinity_polling(none_stop=True)
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"❌ Bot connection failed: {e}")
