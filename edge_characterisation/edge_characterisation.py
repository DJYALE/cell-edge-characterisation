"""
This is the script that shows up in the ImageJ/plugins menu.
The file name *MUST* contain an underscore or it will be hidden!

This boilerplate plugin does pretty clever tricks! Be sure to read:
    https://github.com/swharden/ImageJ-Python-plugin
"""

import sys
import os
import getpass

# edit this folder where this file lives
PLUGIN_DIR= 'edge_characterisation'
PLUGIN_NAME='edge_characterisation'
THIS_FOLDER=os.path.join("/plugins/",PLUGIN_DIR) # with respect to ImageJ.exe

# add your name here to enable developer mode for your user
developerIDs=[
              'scott', # Scott's home computer
              'swharden', # Scott's work computer
              'evenhuis',
              'r.thavindra@gmail.com',]
# if you're unsure what your login name is, uncomment this:
#print("USERNAME IS: [%s]"%getpass.getuser()) 

# set this to False to suppress messages to non-developers
showMessages=True 
              
# from here out it's just Python magic...
if getpass.getuser() in developerIDs:
    print("\n\n~~~ YOU'RE A DEVELOPER! ~~~")
    print("I will recompile python scripts before they run.")
    developer=True
else:
    if showMessages:
        print('User "%s" is not listed as a developer,'%getpass.getuser())
        print("Plugin code is only reloaded when ImageJ restarts.")
    developer=False

# figure out if we are inside ImageJ or in another editor
try:
    from java.lang.System import getProperty # should crash your IDE
    insideImageJ=True
except:
    print("You're running this script OUTSIDE ImageJ's Jython")
    insideImageJ=False
    
# if we are in imagej, allow imports from adjacent files
if insideImageJ:
    fijiDir=os.path.abspath(getProperty('user.dir')+"/")
    thisPath=os.path.abspath(fijiDir+THIS_FOLDER)
    if not os.path.exists(thisPath):
        print("CRITICAL PROBLEM! IMPORT PATH DOESN'T EXIST:")
        print(thisPath+"\n"+"#"*50)
    assert os.path.exists(thisPath)
    if not thisPath in sys.path:
    	# prepend the path so we search in this directory first
    	#sys.path.append(thisPath)
        sys.path = [thisPath]+sys.path  
        if showMessages:
            print("Running inside ImageJ, added import path:\n  "+thisPath)    
    if developer:
        #sys.modules.clear() # forces unloading of all modules
        print( sys.path)
        for fname in [str(x) for x in os.listdir(thisPath) if x.endswith('$py.class')]:
            print(" -- deleting compiled code: %s"%fname)
            os.remove(os.path.join(thisPath,fname))

### THIS IS WHERE YOUR PROGRAM ACTUALLY STARTS ###
def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])

DIALOG_NAME = to_camel_case( PLUGIN_NAME)+"Dialog"
dl = __import__(DIALOG_NAME)
#import curvatureLocalisationDialog as dl # your script without the .py
if __name__=="__main__":
    dl.main()
if __name__=="__builtin__":
    dl.main()

