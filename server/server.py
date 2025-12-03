#!/usr/bin/env python3
# server.py – הגרסה החכמה והמתוקנת לזיהוי עברית מדויק

import socket, threading, sys
from pynput.mouse import Controller as MouseController, Button
import keyboard as kb
import pyautogui
from collections import deque
from thefuzz import process, fuzz 

HOST = '0.0.0.0'
COMMAND_PORT = 5000
DISCOVERY_PORT = 5001
SCROLL_STEP = 100

mouse = MouseController()
scale_value = 1.6667
running = True

# --- מילון הפקודות המלא (כולל הקיצורים החדשים) ---
COMMAND_MAPPINGS = {
    # עכבר
    "RIGHT_CLICK": ["right click", "right", "רייט קליק", "רייט", "ראית", "ימין", "צד ימין"],
    "LEFT_CLICK": ["left click", "left", "לפט קליק", "לפט", "שמאל", "קליק", "תעשה קליק"],
    "SCROLL_DOWN": ["scroll down", "down", "דאון", "למטה", "תרד", "גלילה למטה"],
    "SCROLL_UP": ["scroll up", "up", "אפ", "למעלה", "תעלה", "גלילה למעלה"],
    
    # קיצורים (הוספנו בדיוק את המילים שראית בלוגים)
    "HOTKEY_CTRL_C": ["copy", "העתק", "קופי", "תעתיק", "תעשה העתק"],
    "HOTKEY_CTRL_V": ["paste", "הדבק", "פייסט", "תדביק"],
    "HOTKEY_CTRL_X": ["cut", "גזור", "קאט", "תגזור"],
    "HOTKEY_CTRL_Z": ["undo", "בטל", "אנדו", "חזור אחורה"],
    "HOTKEY_CTRL_S": ["save", "שמור", "סייב", "תשמור"],
    "HOTKEY_ALT_TAB": ["switch", "החלף חלון", "אלט טאב", "טאב", "חלון הבא"],
    "HOTKEY_ENTER": ["enter", "אנטר", "כנס", "שורה חדשה"]
}

def parse_hotkey(name: str):
    parts = name.strip().upper().split('_')
    return [p.lower() for p in parts if p]

def press_combo(keys):
    try:
        combo = '+'.join(keys)
        if combo == 'ctrl+c':
            pyautogui.hotkey('ctrl', 'c')
        else:
            kb.send(combo, do_press=True, do_release=True)
        print(f"✔ Executed Combo: {combo}")
    except Exception as e:
        print(f"❌ Error: {e}")

def handle_internal_command(action):
    if action == "SCROLL_UP":
        mouse.scroll(0, SCROLL_STEP)
    elif action == "SCROLL_DOWN":
        mouse.scroll(0, -SCROLL_STEP)
    elif action == "LEFT_CLICK":
        mouse.click(Button.left)
    elif action == "RIGHT_CLICK":
        mouse.click(Button.right)
    elif action.startswith("HOTKEY_"):
        # חילוץ המקשים מתוך השם (למשל HOTKEY_CTRL_C -> ['ctrl', 'c'])
        key_string = action.replace("HOTKEY_", "")
        keys = parse_hotkey(key_string)
        if keys:
            press_combo(keys)

def handle_smart_voice(text):
    text = text.lower().strip()
    print(f"🔍 Analyzing voice: '{text}'")

    best_score = 0
    best_action = None

    # שלב 1: בדיקה מהירה (בדיוק במילון?)
    for action, keywords in COMMAND_MAPPINGS.items():
        if text in keywords:
            print(f"🎯 Exact match found! '{text}' -> {action}")
            handle_internal_command(action)
            return # מצאנו, סיימנו

    # שלב 2: אם לא מצאנו בול, נפעיל AI
    for action, keywords in COMMAND_MAPPINGS.items():
        match, score = process.extractOne(text, keywords, scorer=fuzz.ratio)
        if score > best_score:
            best_score = score
            best_action = action

    # סף זיהוי (הורדנו ל-60 כדי לתפוס יותר וריאציות)
    if best_score >= 60:
        print(f"🤖 Fuzzy Match: '{text}' -> {best_action} ({best_score}%)")
        handle_internal_command(best_action)
    else:
        print(f"🤷‍♂️ Not understood: '{text}' (Best: {best_action} at {best_score}%)")

def handle_command(cmd: str):
    global scale_value
    try:
        parts = cmd.strip().split(':')
        action = parts[0].strip()

        if action == "VOICE_RAW":
            raw_text = parts[1] if len(parts) > 1 else ""
            handle_smart_voice(raw_text)
            return

        if action == "MOVE_DELTA":
            dx, dy = map(float, parts[1].split(','))
            mouse.move(dx * scale_value, dy * scale_value)

        elif action == "SET_SCALE":
            scale_value = float(parts[1])
            print(f"• Scale set to {scale_value}")

        elif action.startswith("HOTKEY_"):
             # הפעלה ישירה מהכפתורים באפליקציה
             handle_internal_command(action)
        
        else:
            handle_internal_command(action)

    except Exception as e:
        print(f"❌ Error: {e}")

def discovery_listener(sock):
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode().strip() == "DISCOVER":
                sock.sendto(b"MOUSE_SERVER", addr)
        except: pass

def command_listener(sock):
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            if not data: continue
            handle_command(data.decode())
        except: continue

def main():
    global running
    disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    disc_sock.bind((HOST, DISCOVERY_PORT))
    
    cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd_sock.bind((HOST, COMMAND_PORT))
    
    threading.Thread(target=discovery_listener, args=(disc_sock,), daemon=True).start()

    print(f"✅ Server Running (Optimized for Hebrew Commands)")
    print(f"🎤 Recognizes: Copy, Paste, Undo, Enter, Mouse clicks...")
    
    try:
        command_listener(cmd_sock)
    except KeyboardInterrupt:
        running = False
        disc_sock.close()
        cmd_sock.close()

if __name__ == "__main__":
    main()