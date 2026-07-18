#!/usr/bin/env python3
# UptimeRobot Bot - New Signup Page + Railway Deploy (FIXED SELECTORS)
import requests, time, os, subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ===== CONFIG (Railway पर env variables से लेगा) =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8953778114:AAGlkAXZfazrAArDl7vKvbBvp9EuFm91r68")
CHAT_ID = os.getenv("CHAT_ID", "-1004306819565")
OFFSET = 0
user_sessions = {}
driver = None

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': chat_id, 'text': text})
    except Exception as e:
        print(f"Send error: {e}")

# ===== CHROMEDRIVER FINDER =====
def find_chromedriver():
    possible_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/lib/chromium/chromedriver',
        '/snap/bin/chromedriver',
        './chromedriver',
        '/data/data/com.termux/files/usr/bin/chromedriver',
        '/data/data/com.termux/files/usr/lib/chromium/chromedriver',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    try:
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

# ===== DRIVER CREATE =====
def create_driver():
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        print("❌ Chromedriver not found")
        return None
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(chromedriver_path)
    try:
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Driver error: {e}")
        return None

# ===== SIGNUP =====
def signup_uptime(email, password):
    global driver
    if not driver:
        driver = create_driver()
        if not driver:
            return {'error': 'ChromeDriver not found'}
    
    try:
        driver.get('https://dashboard.uptimerobot.com/sign-up')
        time.sleep(3)
        
        wait = WebDriverWait(driver, 20)
        
        # === EMAIL INPUT ===
        email_selectors = [
            (By.CSS_SELECTOR, 'input[type="email"]'),
            (By.CSS_SELECTOR, 'input[name="email"]'),
            (By.XPATH, '//input[@type="email"]'),
            (By.XPATH, '//input[@name="email"]')
        ]
        email_input = None
        for by, selector in email_selectors:
            try:
                email_input = wait.until(EC.presence_of_element_located((by, selector)))
                break
            except:
                continue
        if not email_input:
            return {'error': 'Email input not found'}
        email_input.clear()
        email_input.send_keys(email)
        
        # === PASSWORD INPUT ===
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input.clear()
            password_input.send_keys(password)
        except:
            pass  # कुछ फ्लो में पासवर्ड बाद में माँगते हैं
        
        # === SUBMIT BUTTON ===
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'button.btn-primary'),
            (By.CSS_SELECTOR, 'button.btn'),
            (By.XPATH, '//button[contains(text(), "Register")]'),
            (By.XPATH, '//button[contains(text(), "Sign up")]'),
            (By.XPATH, '//button[contains(text(), "Create")]')
        ]
        submit_btn = None
        for by, selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                break
            except:
                continue
        if not submit_btn:
            return {'error': 'Submit button not found'}
        submit_btn.click()
        time.sleep(5)
        
        # === CHECK RESPONSE ===
        if 'verify' in driver.current_url.lower() or 'otp' in driver.current_url.lower():
            cookies = driver.get_cookies()
            return {'cookies': cookies, 'email': email, 'password': password, 'step': 'otp_required'}
        elif 'dashboard' in driver.current_url.lower():
            cookies = driver.get_cookies()
            return {'cookies': cookies, 'email': email, 'password': password, 'step': 'complete'}
        else:
            # Error check
            error_selectors = [
                (By.CSS_SELECTOR, '.error'),
                (By.CSS_SELECTOR, '.alert-danger'),
                (By.CSS_SELECTOR, '.text-danger'),
                (By.XPATH, '//*[contains(@class, "error")]')
            ]
            for by, selector in error_selectors:
                try:
                    error_elem = driver.find_element(by, selector)
                    if error_elem:
                        return {'error': error_elem.text}
                except:
                    continue
            return {'error': 'Unknown error'}
                
    except Exception as e:
        return {'error': str(e)}

# ===== VERIFY OTP =====
def verify_otp(session_data, otp):
    global driver
    if not driver:
        driver = create_driver()
        if not driver:
            return False
    
    try:
        driver.get('https://dashboard.uptimerobot.com/verify')
        time.sleep(3)
        wait = WebDriverWait(driver, 15)
        
        # === OTP INPUT ===
        otp_selectors = [
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'input[name="otp"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="OTP"]'),
            (By.XPATH, '//input[@name="otp"]')
        ]
        otp_input = None
        for by, selector in otp_selectors:
            try:
                otp_input = wait.until(EC.presence_of_element_located((by, selector)))
                break
            except:
                continue
        if not otp_input:
            return False
        otp_input.clear()
        otp_input.send_keys(otp)
        
        # === SUBMIT ===
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'button.btn-primary'),
            (By.XPATH, '//button[contains(text(), "Verify")]')
        ]
        submit_btn = None
        for by, selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                break
            except:
                continue
        if not submit_btn:
            return False
        submit_btn.click()
        time.sleep(5)
        
        return 'dashboard' in driver.current_url
    except Exception as e:
        print(f"Verify error: {e}")
        return False

# ===== GET UPDATES =====
def get_updates():
    global OFFSET
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={'offset': OFFSET, 'timeout': 30}, timeout=35)
        if r.status_code == 200:
            data = r.json()
            if data['ok'] and data['result']:
                OFFSET = data['result'][-1]['update_id'] + 1
                return data['result']
    except:
        pass
    return []

# ===== MAIN LOOP =====
print("🤖 UptimeRobot Bot Started (New Signup Page + Fixed Selectors)...")
print("📌 Commands: /start, /signup email password, /verify OTP")

while True:
    try:
        for upd in get_updates():
            msg = upd.get('message')
            if not msg:
                continue
            chat_id = msg['chat']['id']
            text = msg.get('text', '').strip()
            
            if text.startswith('/start'):
                send_telegram(chat_id, 
                    "🔓 *UptimeRobot Bot v5.1 (Fixed)*\n"
                    "📌 `/signup email password`\n"
                    "📌 `/verify OTP`\n\n"
                    "✅ नए पेज पर काम करता है!"
                )
            
            elif text.startswith('/signup'):
                parts = text.split()
                if len(parts) < 3:
                    send_telegram(chat_id, "❌ /signup email password")
                    continue
                email, password = parts[1], parts[2]
                send_telegram(chat_id, f"⏳ {email} पर साइनअप हो रहा है...")
                
                result = signup_uptime(email, password)
                
                if result and 'cookies' in result:
                    user_sessions[chat_id] = result
                    if result.get('step') == 'otp_required':
                        send_telegram(chat_id, 
                            f"✅ *साइनअप सफल!*\n📧 {email}\n\n🔑 अब `/verify 123456` करो"
                        )
                    else:
                        send_telegram(chat_id, 
                            f"✅ *अकाउंट एक्टिव!*\n📧 {email}\n🔑 {password}"
                        )
                        send_telegram(CHAT_ID, f"🎯 {email}:{password}")
                        with open("accounts.txt", "a") as f:
                            f.write(f"{email}:{password}\n")
                        del user_sessions[chat_id]
                else:
                    send_telegram(chat_id, f"❌ *फेल!* {result.get('error', 'Unknown error')}")
            
            elif text.startswith('/verify'):
                parts = text.split()
                if len(parts) < 2:
                    send_telegram(chat_id, "❌ /verify 123456")
                    continue
                otp = parts[1]
                if chat_id not in user_sessions:
                    send_telegram(chat_id, "❌ पहले /signup करो")
                    continue
                
                data = user_sessions[chat_id]
                send_telegram(chat_id, "⏳ OTP वेरिफाई हो रहा है...")
                
                if verify_otp(data, otp):
                    send_telegram(chat_id, 
                        f"✅ *अकाउंट एक्टिव!*\n📧 {data['email']}\n🔑 {data['password']}"
                    )
                    send_telegram(CHAT_ID, f"🎯 {data['email']}:{data['password']}")
                    with open("accounts.txt", "a") as f:
                        f.write(f"{data['email']}:{data['password']}\n")
                    del user_sessions[chat_id]
                else:
                    send_telegram(chat_id, "❌ OTP गलत या एक्सपायर!")
        
        time.sleep(2)
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(5)
