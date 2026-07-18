#!/usr/bin/env python3
# UptimeRobot Bot - OTP Mode Fixed (2026)
import requests, time, os, subprocess, threading, logging
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
def find_chromedriver():
    possible_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/lib/chromium/chromedriver',
        '/snap/bin/chromedriver',
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
    
    service = Service(chromedriver_path)
    try:
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.error(f"Driver error: {e}")
        return None

# ===== SIGNUP (OTP REQUIRED) =====
def signup_uptime(email, password):
    global driver
    logger.info(f"🔐 Signup started for: {email}")
    
    if not driver:
        driver = create_driver()
        if not driver:
            return {'error': 'ChromeDriver not found'}
    
    try:
        driver.get('https://dashboard.uptimerobot.com/sign-up')
        time.sleep(3)
        
        wait = WebDriverWait(driver, 20)
        
        # === EMAIL ===
        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
        email_input.clear()
        email_input.send_keys(email)
        logger.info("✅ Email filled")
        
        # === PASSWORD ===
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input.clear()
            password_input.send_keys(password)
            logger.info("✅ Password filled")
        except:
            logger.warning("⚠️ Password field not found - continuing")
        
        # === SUBMIT ===
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        submit_btn.click()
        logger.info("✅ Submit clicked")
        time.sleep(5)
        
        # === CHECK FOR OTP ===
        # OTP पेज पर OTP input दिखना चाहिए
        try:
            otp_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[name="otp"]'))
            )
            logger.info("✅ OTP input found - OTP required!")
            
            # Cookies save
            cookies = driver.get_cookies()
            return {
                'cookies': cookies,
                'email': email,
                'password': password,
                'step': 'otp_required'
            }
        except:
            # अगर OTP input न मिले, तो मैन्युअल डिटेक्शन
            page_text = driver.page_source.lower()
            if 'otp' in page_text or 'verification' in page_text:
                logger.info("✅ OTP detected in page source")
                cookies = driver.get_cookies()
                return {
                    'cookies': cookies,
                    'email': email,
                    'password': password,
                    'step': 'otp_required'
                }
            else:
                # अगर सीधे डैशबोर्ड पर चला गया (शायद ही कभी)
                logger.warning("⚠️ No OTP detected, but proceeding")
                cookies = driver.get_cookies()
                return {
                    'cookies': cookies,
                    'email': email,
                    'password': password,
                    'step': 'otp_required'  # मजबूरन OTP मोड
                }
                
    except Exception as e:
        logger.error(f"❌ Signup error: {e}")
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
        # OTP input ढूंढो और भरो
        wait = WebDriverWait(driver, 15)
        otp_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[name="otp"]')))
        otp_input.clear()
        otp_input.send_keys(otp)
        logger.info("✅ OTP entered")
        
        # Submit करो
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
        submit_btn.click()
        time.sleep(5)
        
        # चेक करो कि डैशबोर्ड पर आ गए या नहीं
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
                        "🔓 *UptimeRobot Bot OTP Mode*\n"
                        "📌 `/signup email password`\n"
                        "📌 `/verify OTP`"
                    )
                
                elif text.startswith('/signup'):
                    parts = text.split()
                    if len(parts) < 3:
                        send_telegram(chat_id, "❌ /signup email password")
                        continue
                    email, password = parts[1], parts[2]
                    send_telegram(chat_id, f"⏳ साइनअप हो रहा है {email}...")
                    
                    result = signup_uptime(email, password)
                    
                    if result and 'cookies' in result:
                        user_sessions[chat_id] = result
                        send_telegram(chat_id, 
                            f"✅ *साइनअप सफल!*\n📧 {email}\n\n🔑 OTP आ गया? `/verify 123456` करो"
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
    logger.info("🚀 Starting UptimeRobot Bot OTP Mode...")
    
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
