#!/usr/bin/env python3
# UptimeRobot Bot - Full Debug + Healthcheck
import requests, time, os, subprocess, threading, logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask

# ===== LOGGING SETUP =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8953778114:AAGlkAXZfazrAArDl7vKvbBvp9EuFm91r68")
CHAT_ID = os.getenv("CHAT_ID", "-1004306819565")
OFFSET = 0
user_sessions = {}
driver = None

# ===== FLASK HEALTHCHECK =====
@app.route('/')
@app.route('/health')
def health():
    logger.info("Healthcheck OK")
    return "OK", 200

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': chat_id, 'text': text})
        logger.info(f"✅ Telegram sent: {text[:50]}...")
    except Exception as e:
        logger.error(f"Send error: {e}")

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
            logger.info(f"✅ Chromedriver found at: {path}")
            return path
    try:
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Chromedriver found via which: {result.stdout.strip()}")
            return result.stdout.strip()
    except:
        pass
    logger.error("❌ Chromedriver NOT found")
    return None

# ===== DRIVER CREATE =====
def create_driver():
    chromedriver_path = find_chromedriver()
    if not chromedriver_path:
        return None
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--disable-logging')
    
    service = Service(chromedriver_path, service_args=['--verbose'])
    try:
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("✅ Driver created successfully")
        return driver
    except Exception as e:
        logger.error(f"❌ Driver error: {e}")
        return None

# ===== SIGNUP =====
def signup_uptime(email, password):
    global driver
    logger.info(f"🔐 Signup started for: {email}")
    
    if not driver:
        driver = create_driver()
        if not driver:
            return {'error': 'ChromeDriver not found'}
    
    try:
        logger.info("📡 Navigating to signup page...")
        driver.get('https://dashboard.uptimerobot.com/sign-up')
        time.sleep(3)
        logger.info(f"📍 Current URL: {driver.current_url}")
        
        # === PAGE SOURCE LOGGING ===
        with open("page_source.html", "w") as f:
            f.write(driver.page_source)
        logger.info("📄 Page source saved to page_source.html")
        
        wait = WebDriverWait(driver, 20)
        
        # === EMAIL INPUT ===
        logger.info("🔍 Looking for email input...")
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
                logger.info(f"✅ Email input found using: {by} - {selector}")
                break
            except Exception as e:
                logger.warning(f"❌ Failed with {by}: {selector} - {str(e)[:50]}")
                continue
        if not email_input:
            return {'error': 'Email input not found'}
        
        email_input.clear()
        email_input.send_keys(email)
        logger.info("✅ Email filled")
        
        # === PASSWORD INPUT ===
        logger.info("🔍 Looking for password input...")
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input.clear()
            password_input.send_keys(password)
            logger.info("✅ Password filled")
        except Exception as e:
            logger.warning(f"⚠️ Password field not found: {e}")
        
        # === SUBMIT BUTTON ===
        logger.info("🔍 Looking for submit button...")
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
                logger.info(f"✅ Submit button found using: {by} - {selector}")
                break
            except Exception as e:
                logger.warning(f"❌ Failed with {by}: {selector} - {str(e)[:50]}")
                continue
        if not submit_btn:
            return {'error': 'Submit button not found'}
        
        logger.info("🖱️ Clicking submit...")
        submit_btn.click()
        time.sleep(5)
        logger.info(f"📍 After submit URL: {driver.current_url}")
        
        # === CHECK RESPONSE ===
        current_url = driver.current_url
        logger.info(f"🔍 Checking response from: {current_url}")
        
        if 'verify' in current_url.lower() or 'otp' in current_url.lower():
            cookies = driver.get_cookies()
            logger.info("✅ OTP required detected")
            return {'cookies': cookies, 'email': email, 'password': password, 'step': 'otp_required'}
        
        elif 'dashboard' in current_url.lower():
            cookies = driver.get_cookies()
            logger.info("✅ Account activated directly (no OTP)")
            return {'cookies': cookies, 'email': email, 'password': password, 'step': 'complete'}
        
        else:
            # Error handling
            logger.warning("⚠️ Unknown page state, checking for errors...")
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
                        error_text = error_elem.text
                        logger.error(f"❌ Error found: {error_text}")
                        return {'error': error_text}
                except:
                    continue
            
            logger.error(f"❌ Unknown error state at: {current_url}")
            return {'error': f'Unknown state: {current_url}'}
                
    except Exception as e:
        logger.error(f"❌ Exception in signup: {str(e)}")
        return {'error': str(e)}

# ===== VERIFY OTP =====
def verify_otp(session_data, otp):
    global driver
    logger.info(f"🔐 Verifying OTP: {otp}")
    if not driver:
        driver = create_driver()
        if not driver:
            return False
    
    try:
        driver.get('https://dashboard.uptimerobot.com/verify')
        time.sleep(3)
        wait = WebDriverWait(driver, 15)
        
        otp_input = None
        otp_selectors = [
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'input[name="otp"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="OTP"]'),
            (By.XPATH, '//input[@name="otp"]')
        ]
        for by, selector in otp_selectors:
            try:
                otp_input = wait.until(EC.presence_of_element_located((by, selector)))
                logger.info(f"✅ OTP input found: {by} - {selector}")
                break
            except:
                continue
        if not otp_input:
            logger.error("❌ OTP input not found")
            return False
        
        otp_input.clear()
        otp_input.send_keys(otp)
        logger.info("✅ OTP entered")
        
        submit_btn = None
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'button.btn-primary'),
            (By.XPATH, '//button[contains(text(), "Verify")]')
        ]
        for by, selector in submit_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                logger.info(f"✅ Verify button found: {by} - {selector}")
                break
            except:
                continue
        if not submit_btn:
            logger.error("❌ Verify button not found")
            return False
        
        submit_btn.click()
        time.sleep(5)
        success = 'dashboard' in driver.current_url
        logger.info(f"✅ Verification {'successful' if success else 'failed'}")
        return success
        
    except Exception as e:
        logger.error(f"❌ Verify error: {e}")
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
    except Exception as e:
        logger.error(f"Get updates error: {e}")
    return []

# ===== TELEGRAM BOT LOOP =====
def bot_loop():
    logger.info("🤖 Telegram Bot Loop Started...")
    while True:
        try:
            updates = get_updates()
            for upd in updates:
                msg = upd.get('message')
                if not msg:
                    continue
                chat_id = msg['chat']['id']
                text = msg.get('text', '').strip()
                logger.info(f"📩 Received: {text}")
                
                if text.startswith('/start'):
                    send_telegram(chat_id, 
                        "🔓 *UptimeRobot Bot v5.3 (Debug)*\n"
                        "📌 `/signup email password`\n"
                        "📌 `/verify OTP`\n\n"
                        "✅ Full logging enabled!"
                    )
                
                elif text.startswith('/signup'):
                    parts = text.split()
                    if len(parts) < 3:
                        send_telegram(chat_id, "❌ /signup email password")
                        continue
                    email, password = parts[1], parts[2]
                    send_telegram(chat_id, f"⏳ साइनअप हो रहा है {email}...\n(चेक करो: Railway Logs में डीटेल है)")
                    
                    result = signup_uptime(email, password)
                    logger.info(f"📊 Signup result: {result}")
                    
                    if result and 'cookies' in result:
                        user_sessions[chat_id] = result
                        if result.get('step') == 'otp_required':
                            send_telegram(chat_id, 
                                f"✅ *साइनअप सफल!*\n📧 {email}\n\n🔑 अब `/verify 123456` करो"
                            )
                        else:
                            send_telegram(chat_id, 
                                f"✅ *अकाउंट एक्टिव!*\n📧 {email}\n🔑 {password}\n\nबिना OTP के बन गया!"
                            )
                            send_telegram(CHAT_ID, f"🎯 {email}:{password}")
                            with open("accounts.txt", "a") as f:
                                f.write(f"{email}:{password}\n")
                            del user_sessions[chat_id]
                    else:
                        error_msg = result.get('error', 'Unknown error') if result else 'No result'
                        send_telegram(chat_id, f"❌ *फेल!*\n{error_msg}")
                        logger.error(f"❌ Signup failed: {error_msg}")
                
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
            logger.error(f"Loop error: {e}")
            time.sleep(5)

# ===== MAIN =====
if __name__ == "__main__":
    logger.info("🚀 Starting UptimeRobot Bot with Full Debugging...")
    
    # Start bot thread
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    # Start Flask
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🌐 Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
