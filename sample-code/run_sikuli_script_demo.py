from selenium import webdriver
from os import path

driver = webdriver.Remote( command_executor='http://127.0.0.1:4723/wd/hub', desired_capabilities={'browserName':'Sikuli'})
print "Desired Capabilities returned by server:\n"
print driver.desired_capabilities
print ""

# execute a Sikuli script file (rather than call specific Sikuli API commands)
# supply path to Sikuli script file followed by optional arguments
driver.execute_script(os.path.join(os.path.curdir,"demo.skl"),"hello","world")
driver.quit()