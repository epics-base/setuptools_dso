import sys, os

def fixpath():
    path = os.environ.get('PATH', '').split(os.pathsep)
    libdir = os.path.join(os.path.dirname(__file__), 'lib')
    path.append(libdir)
    os.environ['PATH'] = os.pathsep.join(path)

    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(libdir)

if sys.platform == "win32":
    fixpath()
