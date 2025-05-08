import time
import psutil
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import win32gui, win32con  # Requires pywin32
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


def launch_sap():
    sap_url = "website_SAP_Fiori_URL" # Change this as required
    driver = configure_driver()
    driver.get(sap_url)
    print(f"Opened URL: {sap_url}")

    # STEP 1: Click the Main Tab "SAP GUI Launchpad Wieland S/4"
    tab_xpath = '//h2[@title="SAP GUI Launchpad <Company Name> S/4"]' # Change this as required
    for attempt in range(3):
        try:
            # Wait for page and tab to be ready
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            tab_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, tab_xpath))
            )

            # Scroll and click with retry logic
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", tab_element)
            time.sleep(0.5)

            try:
                ActionChains(driver).move_to_element(tab_element).pause(0.5).click().perform()
                print('Clicked main tab successfully')
                break
            except:
                driver.execute_script("arguments[0].click();", tab_element)
                print('Used JS click as fallback')
                break

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == 2:
                driver.quit()
                raise Exception("Failed to click main tab after 3 attempts")
            time.sleep(1)

    # STEP 2: Click the WWP 001 tile - using more reliable selectors from the HTML
    tile_locator = (By.CSS_SELECTOR, 'a[aria-label*="<Enter tile name here>"][aria-label*="<Enter label here>"]') # Change this as per the information on the tile on Fiori web page

    for attempt in range(3):
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(tile_locator)
            )

            tile = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(tile_locator)
            )

            # Smooth scroll and click with multiple fallbacks
            driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            """, tile)

            time.sleep(0.5)  # Allow scrolling to complete

            try:
                ActionChains(driver).move_to_element(tile).pause(0.3).click().perform()
                print("Clicked tile using ActionChains")
            except:
                driver.execute_script("arguments[0].click();", tile)
                print("Clicked tile using JavaScript")

            # Verify click took effect
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            break

        except Exception as e:
            print(f"Tile click attempt {attempt + 1} failed: {str(e)}")
            if attempt == 2:
                driver.quit()
                raise Exception("Failed to click tile after 3 attempts")
            time.sleep(1)

    # STEP 3: SAP Logon verification
    time.sleep(10)
    if is_saplogon_running():
        print("SAP logon.exe launched successfully")
        minimize_sap_window()
        result = True
    else:
        print("SAP logon.exe failed to launch")
        result = False

    driver.quit()
    return result




def configure_driver():
    """
    Configures and returns a Selenium WebDriver for Microsoft Edge.
    """
    options = webdriver.EdgeOptions()
    # Instead of starting minimized, do not add the "start-minimized" argument.
    # You could maximize or leave it at its default size:
    options.add_argument("start-maximized")
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    driver.implicitly_wait(5)
    return driver

def minimize_sap_window():
    """
    Attempts to find the SAP Logon window and minimize it.
    You may need to adjust the window title to match your SAP Logon window.
    """
    # Example: if your SAP Logon window title is "SAP Logon 750"
    window_title = "SAP Logon"  # Adjust as needed
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        print("SAP window minimized.")
    else:
        print("SAP window not found; unable to minimize.")

def is_saplogon_running():
    """
    Checks if the process 'saplogon.exe' is running on the system.
    """
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == 'saplogon.exe':
                return True
        except Exception:
            continue
    return False


if __name__ == "__main__":
    try:
        if launch_sap():
            print("SAP Desktop Application launched and minimized successfully.")
        else:
            print("Failed to detect SAP Desktop Application.")
    except Exception as err:
        print(f"An error occurred: {err}")
