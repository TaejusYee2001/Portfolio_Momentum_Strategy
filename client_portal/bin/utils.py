import os
import time
import signal
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


process = None

def get_child_processes(parent_pid):
    """Return a list of child PIDs of the given parent PID."""
    try:
        result = subprocess.run(
            ['ps', '--ppid', str(parent_pid), '-o', 'pid='],
            stdout=subprocess.PIPE,
            text=True
        )
        child_pids = [int(pid) for pid in result.stdout.split() if pid]
        return child_pids
    except Exception as e:
        print(f"Error getting child processes: {e}")
        return []

def start_client_portal():
    global process
    
    os.chdir('client_portal')  

    process = subprocess.Popen(['bin/run.sh', 'root/conf.yaml'])
    
    time.sleep(1)
    print(f"Client portal started with PID: {process.pid}")


def stop_client_portal():
    global process
    
    if process:
        parent_pid = process.pid
        try:
            child_pids = get_child_processes(parent_pid)
            
            for pid in child_pids:
                print(f"Terminating child process {pid}")
                os.kill(pid, signal.SIGTERM)

            time.sleep(1)
            
            print(f"Terminating parent process {parent_pid}")
            process.terminate()
            
            return_code = process.wait(timeout=10)
            print(f"Parent process stopped gracefully with return code {return_code}.")
        
        except subprocess.TimeoutExpired:
            print(f"Parent process did not terminate gracefully. Killing it.")
            process.kill()
            return_code = process.wait()
            print(f"Parent process forcibly stopped with return code {return_code}.")
        
        except Exception as e:
            print(f"Error stopping process: {e}")
    else:
        print("No process to stop.")

def login_client_portal(paper_username, paper_password):
    
    # Configure Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignore certificate errors
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    chrome_options.add_argument("--no-sandbox")  # Disable sandboxing (useful for certain environments)
    chrome_options.add_argument("--window-size=1920,1080")  # Set a specific window size
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--headless")  # Uncomment if you want to run in headless mode
    chrome_options.add_argument("--disable-infobars")  # Disable the "Chrome is being controlled by automated test software" infobar
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to the login page
        driver.get('https://localhost:5000/sso/Login?forwardTo=22&RL=1&ip2loc=US')

        username_input = driver.find_element(By.CSS_SELECTOR, '#xyz-field-username')
        username_input.send_keys(paper_username)

        # Find the password input element and enter the password
        password_input = driver.find_element(By.CSS_SELECTOR, '#xyz-field-password')
        password_input.send_keys(paper_password)

        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body > pre'))
        )
        
    finally:
        driver.quit()
        print("successfully logged in")
