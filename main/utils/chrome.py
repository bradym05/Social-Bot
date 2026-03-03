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
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--password-store=basic")
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        },
    )
    # Create driver
    driver = webdriver.Chrome(options=options)
    # Use CDP to override device metrics natively
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width":0,
        "height":0,
        "deviceScaleFactor": 1.25, 
        "mobile": False
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    # Custom scripts
    remove_cdp_props(driver)

    return driver
