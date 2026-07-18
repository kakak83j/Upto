#!/usr/bin/env python3
# UptimeRobot Bot - Full Registration + OTP (2026)
import requests, time, os, threading, logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask

# ===== LOGGING =====
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
    return "OK", 200

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': chat_id, 'text': text})
    except Exception as e:
        logger.error(f"Send error: {e}")

# ===== CHROMEDRIVER =====
def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        service = Service('/usr/bin/chromedriver')
        return webdriver.Chrome(service=service, options=options)
    except:
        try:
            service = Service('chromedriver')
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"Driver error: {e}")
            return None

# ===== SIGNUP + OTP =====
def signup_and_otp(email, password):
    global driver
    logger.info(f"🔐 Starting full signup for: {email}")
    
    if not driver:
        driver = create_driver()
        if not driver:
            return {'error': 'ChromeDriver not found'}
    
    try:
        # === STEP 1: Signup Page ===
        logger.info("📡 Navigating to signup...")
        driver.get('https://dashboard.uptimerobot.com/sign-up')
        time.sleep(3)
        wait = WebDriverWait(driver, 20)
        
        # === STEP 2: Email ===
        logger.info("📧 Filling email...")
        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
        email_input.clear()
        email_input.send_keys(email)
        logger.info("✅ Email filled")
        
        # === STEP 3: Password ===
        logger.info("🔑 Filling password...")
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input.clear()
            password_input.send_keys(password)
            logger.info("✅ Password filled")
        except:
            logger.warning("⚠️ Password field not found - continuing")
        
        # === STEP 4: Submit ===
        logger.info("🖱️ Clicking submit...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        submit_btn.click()
        logger.info("✅ Submit clicked")
        time.sleep(5)
        
        # === STEP 5: Check if OTP appeared ===
        logger.info("🔍 Checking for OTP...")
        try:
            # OTP input ढूंढो
            otp_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[name="otp"]'))
            )
            logger.info("✅ OTP input found!")
            
            # Cookies save
            cookies = driver.get_cookies()
            return {
                'cookies': cookies,
                'email': email,
                'password': password,
                'step': 'otp_required',
                'driver': driver
            }
        except:
            # अगर OTP input न मिले, तो पेज सोर्स चेक करो
            page_text = driver.page_source.lower()
            if 'otp' in page_text or 'verification' in page_text:
                logger.info("✅ OTP detected in page source")
                cookies = driver.get_cookies()
                return {
                    'cookies': cookies,
                    'email': email,
                    'password': password,
                    'step': 'otp_required',
                    'driver': driver
                }
            else:
                # अगर कुछ और हो
                logger.error("❌ OTP not found!")
                return {'error': 'OTP page not loaded'}
                
    except Exception as e:
        logger.error(f"❌ Signup error: {e}")
        return {'error': str(e)}

# ===== VERIFY OTP =====
def verify_otp(otp):
    global driver
    logger.info(f"🔐 Verifying OTP: {otp}")
    
    if not driver:
        return False
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # === STEP 1: OTP Input ===
        logger.info("🔍 Finding OTP input...")
        otp_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[name="otp"]')))
        otp_input.clear()
        otp_input.send_keys(otp)
        logger.info("✅ OTP entered")
        
        # === STEP 2: Submit OTP ===
        logger.info("🖱️ Clicking verify...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        submit_btn.click()
        time.sleep(5)
        
        # === STEP 3: Check Success ===
        if 'dashboard' in driver.current_url:
            logger.info("✅ OTP verified - Dashboard reached!")
            return True
        else:
            # Error check
            try:
                error_elem = driver.find_element(By.CSS_SELECTOR, '.error, .alert-danger')
                logger.error(f"❌ OTP error: {error_elem.text}")
                return False
            except:
                logger.error("❌ OTP verification failed")
                return False
                
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
    except:
        pass
    return []

# ===== BOT LOOP =====
def bot_loop():
    logger.info("🤖 Bot loop started")
    while True:
        try:
            for upd in get_updates():
                msg = upd.get('message')
                if not msg:
                    continue
                chat_id = msg['chat']['id']
                text = msg.get('text', '').strip()
                logger.info(f"📩 Received: {text}")
                
                if text.startswith('/start'):
                    send_telegram(chat_id, 
                        "🔓 *UptimeRobot Bot - Full Registration*\n"
                        "📌 `/signup email password`\n"
                        "📌 `/verify OTP`\n\n"
                        "बोट खुद registration करेगा और OTP माँगेगा!"
                    )
                
                elif text.startswith('/signup'):
                    parts = text.split()
                    if len(parts) < 3:
                        send_telegram(chat_id, "❌ /signup email password")
                        continue
                    email, password = parts[1], parts[2]
                    send_telegram(chat_id, f"⏳ Registration हो रही है {email}...\n(इसमें 1-2 मिनट लग सकते हैं)")
                    
                    result = signup_and_otp(email, password)
                    
                    if result and 'cookies' in result:
                        user_sessions[chat_id] = result
                        send_telegram(chat_id, 
                            f"✅ *Registration सफल!*\n📧 {email}\n\n🔑 OTP आ गया? `/verify 123456` करो"
                        )
                    else:
                        error = result.get('error', 'Unknown error') if result else 'No result'
                        send_telegram(chat_id, f"❌ *फेल!*\n{error}")
                
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
                    
                    if verify_otp(otp):
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
    logger.info("🚀 Starting UptimeRobot Bot Full Registration...")
    
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
