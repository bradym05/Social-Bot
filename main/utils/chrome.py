from selenium import webdriver

def remove_cdp_props(driver):
    """
    Removes CDP props from a webdriver instance, permanently
    - Implementation from: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/986
    """
    # Get list of props
    cdc_props = driver.execute_script('const j=[];for(const p in window){'
                                    'if(/^[a-z]{3}_[a-zA-Z0-9]{22}_.*/i.test(p)){'
                                    'j.push(p);delete window[p];}}return j;')
    # Check if any cdc props are presnt
    if len(cdc_props) > 0:
        cdc_props_js_array = '[' + ','.join('"' + p + '"' for p in cdc_props) + ']'
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',
                            {'source': cdc_props_js_array + '.forEach(k=>delete window[k]);'})

def no_indicators():
    """
    Returns a webdriver instance with:
    - Automation indicators removed (https://www.zenrows.com/blog/selenium-avoid-bot-detection#disable-automation-indicator-webdriver-flags)
    - CDP properties removed (https://github.com/dobiadi/bot-detect/blob/master/src/collector/detections/chromedriver/README.md)
    """
    # Setup options
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False)
    # Create and return driver
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    # Custom scripts
    remove_cdp_props(driver)
    return driver
