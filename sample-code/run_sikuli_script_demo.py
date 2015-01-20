from selenium import webdriver
import os

driver = webdriver.Remote( command_executor='http://127.0.0.1:4723/wd/hub', desired_capabilities={'browserName':'Sikuli'})
print "Desired Capabilities returned by server:\n"
print driver.desired_capabilities
print ""

# execute a Sikuli script file (rather than call specific Sikuli API commands)
# supply path to Sikuli script file followed by optional arguments
driver.execute_script("C:\\PathOnSikuliDriverServerHostMachineTo\\demo.skl","Hello","World")
# or on Linux/Mac:
#driver.execute_script("/PathOnSikuliDriverServerHostMachineTo/demo.skl","Hello","World")

# can opt to use demo.sikuli as well over demo.skl, but I prefer skl version

driver.quit()