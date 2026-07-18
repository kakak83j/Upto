#!/usr/bin/env python3
# UptimeRobot Bot - Fixed Selectors for New Page
import requests, time, os, subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BOT_TOKEN = os.getenv("BOT_TOKEN", "8953778114:AAGlkAXZfazrAArDl7vKvbBvp9EuFm91r68")
CHAT_ID = os.getenv("CHAT_ID", "-1004306819565")
OFFSET = 0
user_sessions = {}
driver = None

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': chat_id, 'text': text})
    except Exception as e:
        print(f"Send error: {e}")

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
        
        # Email input - multiple possible selectors
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
        
        # Password input (if exists)
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password_input.clear()
            password_input.send_keys(password)
        except:
            pass
        
        # Submit button - multiple possible selectors
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
        
        # Check response
        if 'verify' in driver.current_url.lower() or 'otp' in driver.current_url.lower():
            cookies = driver.get_cookies()
            return {
                'cookies': cookies,
                'email': email,
                'password': password,
                'step': 'otp_required'
            }
        elif 'dashboard' in driver.current_url.lower():
            cookies = driver.get_cookies()
            return {
                'cookies': cookies,
                'email': email,
                'password': password,
                'step': 'complete'
            }
        else:
            # Check for error messages
            error_selectors = [
                (By.CSS_SELECTOR, '.error'),
                (By.CSS_SELECTOR, '.alert-danger'),
                (By.CSS_SELECTOR, '.text-danger'),
                (By.XPATH, '//*[contains(@class, "error")]'),
                (By.XPATH, '//*[contains(@class, "alert")]')
            ]
            
            for by, selector in error_selectors:
                try:
                    error_elem = driver.find_element(by, selector)
                    if error_elem:
                        return {'error': error_elem.text}
                except:
                    continue
            
            return {'error': 'Unknown error—check logs'}
                
    except Exception as e:
        return {'error': str(e)}

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
        
        # OTP input
        otp_selectors = [
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'input[name="otp"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="OTP"]'),
            (By.XPATH, '//input[@name="otp"]'),
            (By.XPATH, '//input[@type="text"]')
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
        
        # Submit button
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'button.btn-primary'),
            (By.XPATH, '//button[contains(text(), "Verify")]'),
            (By.XPATH, '//button[contains(text(), "Confirm")]')
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

# Rest of the bot code remains the same (get_updates, main loop)...
