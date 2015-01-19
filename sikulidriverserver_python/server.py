#    Source code is modified from and based off of 
#    old/original Appium Python implementation at
#
#    https://github.com/hugs/appium-old
#
#    Licensed to the Apache Software Foundation (ASF) under one
#    or more contributor license agreements.  See the NOTICE file
#    distributed with this work for additional information
#    regarding copyright ownership.  The ASF licenses this file
#    to you under the Apache License, Version 2.0 (the
#    "License"); you may not use this file except in compliance
#    with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an
#    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#    KIND, either express or implied.  See the License for the
#    specific language governing permissions and limitations
#    under the License.

from bottle import Bottle, request, response, redirect
from bottle import run, static_file
import ConfigParser
import socket
import sys
import platform
import os
import subprocess
import base64
import urllib
from org.sikuli.script import Button, Env, Key, KeyModifier, Match, Pattern, Region, Screen
from org.sikuli.script import ScreenImage #, SikuliScript
# can comment out/remove below JysonCodec reference if using Jython 2.7+
#from com.xhaus.jyson import JysonCodec as json
#import com.xhaus.jyson.JysonCodec as json

app = Bottle()

@app.get('/favicon.ico')
def get_favicon():
    return static_file('favicon.ico', root='.')

def get_platform():
    if sys.platform == "win32":
        if platform.release() == "Vista":
            wd_platform = "VISTA"
        elif platform.release() == "XP": #?
            wd_platform = "XP"
        else:
            wd_platform = "WINDOWS"
    elif sys.platform == "darwin":
        wd_platform = "MAC"
    else: #sys.platform.startswith('linux'):
        wd_platform = "LINUX"
    return wd_platform

@app.route('/wd/hub/status', method='GET')
def status():
    wd_platform = get_platform()
    status = {'sessionId': app.SESSION_ID if app.started else None,
              'status': 0,
              'value': {'build': {'version': 'SikuliDriverServer 0.1'}, 
              'os': {'arch':platform.machine(),'name':wd_platform,'version':platform.release()}}}
    return status

@app.route('/wd/hub/session', method='POST')
def create_session():
    print "in session"
    #process desired capabilities
    request_data = request.body.read()
    dc = json.loads(request_data).get('desiredCapabilities')
    if dc is not None:
        newSimilarity = dc.get('imageRecognitionSimilarityValue')
        if newSimilarity is not None:
            app.similarity = newSimilarity
        newImageFolder = dc.get('defaultImageFolder')
        if newImageFolder is not None:
            app.image_path = newImageFolder
        newConfigFile = dc.get('defaultElementImageMapConfigFile')
        if newConfigFile is not None:
            app.element_locator_map_file = newConfigFile
    print "checked dc"
    #setup session
    app.started = True
    redirect('/wd/hub/session/%s' % app.SESSION_ID)

@app.route('/wd/hub/session/<session_id>', method='GET')
def get_session(session_id=''):
    wd_platform = get_platform()
    app_response = {'sessionId': session_id,
                'status': 0,
                'value': {"version":"0.1",
                          "browserName":"Sikuli",
                          "platform":wd_platform,
                          "takesScreenshot":True,
                          "imageRecognitionSimilarityValue":app.similarity,
                          "defaultImageFolder":app.image_path,
                          "defaultElementImageMapConfigFile":app.element_locator_map_file}}
    return app_response

@app.route('/wd/hub/session/<session_id>', method='DELETE')
def delete_session(session_id=''):
    app.started = False
    app_response = {'sessionId': session_id,
                'status': 0,
                'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/execute', method='POST')
def execute_script(session_id=''):
    request_data = request.body.read()
    try:
        script = json.loads(request_data).get('script')
        args = json.loads(request_data).get('args')

        wd_platform = get_platform()
        # Sikuli IDE executor commands may have to be updated should syntax change in future release
        if wd_platform == "WINDOWS":
            sikuliIdeRunner = os.path.join(app.sikuli_ide_dir,"runIDE.cmd")
        elif wd_platform == "MAC":
            sikuliIdeRunner = os.path.join(app.sikuli_ide_dir,"SikuliX-IDE.app/Contents/runIDE")
        else: # Linux
            # I have not tested on Linux, will do later, or someone help test/confirm
            sikuliIdeRunner = os.path.join(app.sikuli_ide_dir,"sikuli-ide.jar/runIDE")

        script_call = "%s -r %s" % (sikuliIdeRunner,script)
        if args is not None:
            script_call = "%s --" % script_call
            for arg in args:
                script_call = "%s %s" % (script_call,arg)
        print "script2exec: %s" % script_call
        os.system(script_call)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[1])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/element/<element_id>/click', method='POST')
def element_click(session_id='', element_id=''):
    try:
        #img = decode_value_from_wire(element_id)
        #app.SS.click(img)
        app.SS.click(app.element_list[element_id])
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/doubleclick', method='POST')
def double_click(session_id=''):
    try:
        current_location = Env.getMouseLocation()
        app.SS.doubleClick(current_location)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/click', method='POST')
def mouse_click(session_id=''):
    request_data = request.body.read()
    if request_data == None or request_data == '' or request_data == "{}":
        button = 0
    else:
        button = json.loads(request_data).get('button')
    try:
        current_location = Env.getMouseLocation()
        if button == 1:
            app.SS.mouseMove(current_location)
            app.SS.mouseDown(app.Buttons.MIDDLE)
            app.SS.mouseUp(app.Buttons.MIDDLE)
        elif button == 2:
            app.SS.rightClick(current_location)
        else: #button 1
            app.SS.click(current_location)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/buttonup', method='POST')
def mouse_up(session_id=''):
    request_data = request.body.read()
    if request_data == None or request_data == '' or request_data == "{}":
        button = 0
    else:
        button = json.loads(request_data).get('button')
    try:
        if button == 1:
           app.SS.mouseUp(app.Buttons.MIDDLE)
        elif button == 2:
            app.SS.mouseUp(app.Buttons.RIGHT)
        else: #button 1
            app.SS.mouseUp(app.Buttons.LEFT)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/buttondown', method='POST')
def mouse_down(session_id=''):
    request_data = request.body.read()
    if request_data == None or request_data == '' or request_data == "{}":
        button = 0
    else:
        button = json.loads(request_data).get('button')
    try:
        if button == 1:
            app.SS.mouseDown(app.Buttons.MIDDLE)
        elif button == 2:
            app.SS.mouseDown(app.Buttons.RIGHT)
        else: #button 1
            app.SS.mouseDown(app.Buttons.LEFT)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/moveto', method='POST')
def move_to(session_id=''):
    request_data = request.body.read()
    if request_data == None or request_data == '' or request_data == "{}":
        element_id = None
        xoffset = None
        yoffset = None
    else:
        element_id = json.loads(request_data).get('element')
        xoffset = json.loads(request_data).get('xoffset')
        yoffset = json.loads(request_data).get('yoffset')
    try:
        if element_id == None and (xoffset != None or yoffset != None):
            mouse_pos = Env.getMouseLocation()
            app.SS.mouseMove(Location(mouse_pos.getX()+xoffset,mouse_pos.getY()+yoffset))
        else:
            if xoffset != None or yoffset != None:
                #img = decode_value_from_wire(element_id)
                #app.SS.exists(img)
                #elem_pos = Region.getLastMatch().getTopLeft()
                elem_pos = app.element_list[element_id].getTopLeft()
                app.SS.mouseMove(Location(elem_pos.getX()+xoffset,elem_pos.getY()+yoffset))
            else: # just go to center of element
                #img = decode_value_from_wire(element_id)
                #app.SS.exists(img)
                #elem_pos = Region.getLastMatch().getCenter()
                elem_pos = app.element_list[element_id].getCenter()
                app.SS.mouseMove(Location(elem_pos.getX(),elem_pos.getY()))
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/element/<element_id>/value', method='POST')
def set_value(session_id='', element_id=''):
    request_data = request.body.read()
    try:
        value_to_set = json.loads(request_data).get('value')
        value_to_set = ''.join(value_to_set)
        #img = decode_value_from_wire(element_id)
        #app.SS.type(img, value_to_set)
        app.SS.type(app.element_list[element_id],value_to_set)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/element/<element_id>/text', method='GET')
def get_text_on_element(session_id='', element_id=''):
    try:
        result = app.element_list[element_id].text()
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}
    
    app_response = {'sessionId': session_id,
        'status': 0,
        'value': result}
    return app_response

@app.route('/wd/hub/session/<session_id>/element/<element_id>/elements', method='POST')
def element_find_elements(session_id='', element_id=''):
    return _find_element(session_id, element_id, many=True)

@app.route('/wd/hub/session/<session_id>/elements', method='POST')
def find_elements(session_id=''):
    return _find_element(session_id, "root", many=True)

@app.route('/wd/hub/session/<session_id>/element/<element_id>/element', method='POST')
def element_find_element(session_id='', element_id=''):
    return _find_element(session_id, element_id)

@app.route('/wd/hub/session/<session_id>/element', method='POST')
def find_element(session_id=''):
    return _find_element(session_id, "root")

def _find_element(session_id, context, many=False):
    try:
        json_request_data = json.loads(request.body.read())
        locator_strategy = json_request_data.get('using')
        value = json_request_data.get('value')

        if locator_strategy == "id":
            path = app.config.get("Element Mapping",value)
        elif locator_strategy == "name":
            path = os.path.join(app.image_path,value)
        elif locator_strategy == "xpath":
            path = value
        else:
            response.status = 501
            return {'sessionId': session_id, 'status': 32, 'value': 'Unsupported location strategy, use id, name, or XPath only. See docs for details.'}
        elem = Pattern(path).similar(app.similarity)

        if not many:
            try:
                if context == "root":
                    result = app.SS.find(elem)
                else:
                    result = app.element_list[context].find(elem)
            except:
                return {'sessionId': session_id, 'status': 7, 'value': 'Element not found'}
            #found_elements = {'ELEMENT':encode_value_4_wire(path)}
            app.element_list.append(result)
            found_elements = {'ELEMENT':app.element_counter}            
            app.element_counter = app.element_counter + 1
        else:
            try:
                if context == "root":
                    result = app.SS.findAll(elem)
                else:
                    result = app.element_list[context].findAll(elem)
                temp_elements = []
                while result.hasNext(): # loop as long there is a first and more matches
                    app.element_list.append(result.next())
                    temp_elements.append({'ELEMENT':app.element_counter})
                    app.element_counter = app.element_counter + 1
                found_elements = temp_elements                    
            except:
                found_elements = []            
        return {'sessionId': session_id, 'status': 0, 'value': found_elements}
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

@app.route('/wd/hub/session/<session_id>/screenshot', method='GET')
def get_screenshot(session_id=''):
    try:
        path = app.SS.capture(app.SS.getBounds())
        with open(path, 'rb') as screenshot:
            encoded_file = base64.b64encode(screenshot.read())
        return {'sessionId': session_id, 'status': 0, 'value': encoded_file}
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

@app.route('/wd/hub/session/<session_id>/element/<element_id>/displayed', method='GET')
def element_displayed(session_id='', element_id=''):
    try:
        #img = decode_value_from_wire(element_id)
        #result = app.SS.exists(img)
        result = app.SS.exists(app.element_list[element_id])
        displayed = True if result is not None else False
        return {'sessionId': session_id, 'status': 0, 'value': displayed}
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

@app.route('/wd/hub/session/<session_id>/element/<element_id>/location', method='GET')
def element_location(session_id='', element_id=''):
    try:
        #img = decode_value_from_wire(element_id)
        #result = app.SS.exists(img)
        #elem_pos = Region.getLastMatch().getTopLeft()
        elem_pos = app.element_list[element_id].getTopLeft()
        location = {'x': elem_pos.getX(), 'y': elem_pos.getY()}
        return {'sessionId': session_id, 'status': 0, 'value': location}
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}
    
@app.route('/wd/hub/session/<session_id>/element/<element_id>/size', method='GET')
def element_size(session_id='', element_id=''):
    try:
        #img = decode_value_from_wire(element_id)
        #result = app.SS.exists(img)
        #width = Region.getLastMatch().getW()
        #height = Region.getLastMatch().getH()
        width = app.element_list[element_id].getW()
        height = app.element_list[element_id].getH()
        size = {'width': width, 'height': height}
        return {'sessionId': session_id, 'status': 0, 'value': size}
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

@app.route('/wd/hub/session/<session_id>/file', method='POST')
def upload_file(session_id=''):
    try:
        request_data = request.body.read()
        b64data = json.loads(request_data).get('file')
        byteContent = base64.b64decode(b64data)
        path = os.tempnam()
        with open(path, 'wb') as f:
            f.write(byteContent)
        extracted_files = unzip(path,os.path.dirname(path))        
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}

    # For (remote) file uploads - well currently SikuliDriverServer will always be "remote"
    # we can't formally/technically support multiple file uploads yet, due to Selenium issue 2239
    # as the WebDriver/JSONWireProtocol spec doesn't define how to handle request/response
    # of multiple files uploaded. Therefore, we assume user upload single file for now
    result = "".join(extracted_files)
    app_response = {'sessionId': session_id,
        'status': 0,
        'value': result}
    return app_response

def unzip(source_filename, dest_dir):
    import zipfile,os.path
    files_in_zip = []
    with zipfile.ZipFile(source_filename) as zf:        
        for member in zf.infolist():
            words = member.filename.split('/')
            path = dest_dir
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)
            unzipped_file = os.path.join(dest_dir,member.filename)
            print "Unzipped a file: %s" % unzipped_file
            files_in_zip.append(unzipped_file)
    return files_in_zip

@app.route('/wd/hub/session/<session_id>/timeouts/implicit_wait', method='POST')
def set_timeout(session_id=''):
    try:
        request_data = request.body.read()
        new_timeout = json.loads(request_data).get('ms')
        # we need to handle timeout as seconds, less than 1 sec = no timeout then
        if new_timeout < 1000:
            app.SS.setAutoWaitTimeout(0)
        else:
            app.SS.setAutoWaitTimeout(new_timeout/1000)
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}
    
    app_response = {'sessionId': session_id,
        'status': 0,
        'value': {}}
    return app_response

@app.route('/wd/hub/session/<session_id>/source', method='GET')
def get_text_on_screen(session_id=''):
    try:
        result = app.SS.text()
    except:
        response.status = 400
        return {'sessionId': session_id, 'status': 13, 'value': str(sys.exc_info()[0])}
    
    app_response = {'sessionId': session_id,
        'status': 0,
        'value': result}
    return app_response

@app.error(404)
def unsupported_command(error):
    response.content_type = 'text/plain'
    return 'Unrecognized command, or SikuliDriverServer does not support/implement this: %s %s' % (request.method, request.path)

def encode_value_4_wire(value):
    return urllib.pathname2url(base64.b64encode(value))

def decode_value_from_wire(value):
    return base64.b64decode(urllib.url2pathname(value))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='SikuliDriverServer - a webdriver-compatible server for use with desktop GUI automation via Sikuli library/tool.')
    #parser.add_argument('-v', dest='verbose', action="store_true", default=False, help='verbose mode')
    parser.add_argument('-a', '--address', type=str, default=None, help='ip address to listen on')
    parser.add_argument('-p', '--port', type=int, default=4723, help='port to listen on')
    parser.add_argument('-s', '--similarity', type=float, default=0.7, help='define similarity value for finding elements via images files, see docs for details')
    parser.add_argument('-t', '--timeout', type=float, default=0, help='define timeout for finding elements via images files, see docs for details')
    parser.add_argument('-f', '--images_folder', type=str, default=None, help='define image folder containing element locator images for find by name, defaults to image subfolder within the app/server directory')
    parser.add_argument('-c', '--element_image_mapping_file',  type=str, default=None, help='define the element image mapping config file for find by ID, see default sample config file in the app/server directory')
    parser.add_argument('-i', '--sikuli_ide_dir',  type=str, default=None, help='defines the directory containing Sikuli IDE for executing Sikuli scripts')

    args = parser.parse_args()
    
    if args.address is None:
        try:
            args.address = socket.gethostbyname(socket.gethostname())
        except:
            args.address = '127.0.0.1'
    
    if args.element_image_mapping_file is not None:
        app.element_locator_map_file = args.element_image_mapping_file
    else:
        app.element_locator_map_file = os.path.join(os.path.curdir,'element_image_map.cfg')
    if args.images_folder is not None:
        app.image_path = args.images_folder
    else:
        app.image_path = os.path.join(os.path.curdir,'images')
    if args.sikuli_ide_dir is not None:
        app.sikuli_ide_dir = args.sikuli_ide_dir
    else:
        app.sikuli_ide_dir = os.path.curdir
    app.similarity = args.similarity
    app.timeout = args.timeout

    app.config = ConfigParser.RawConfigParser()
    app.config.read(app.element_locator_map_file)
    app.SS = Screen()
    app.PT = Pattern()
    app.Buttons = Button()
    app.Keys = Key()
    app.KeyMods = KeyModifier()
    app.SS.setAutoWaitTimeout(app.timeout)
    app.element_counter = 0
    app.element_list = []

    app.SESSION_ID = "%s:%d" % (args.address, args.port)
    app.started = False
    run(app, host=args.address, port=args.port)
