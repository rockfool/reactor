# Boilerplate to add ../pythonlibs (via full path resolution) to import paths
import os,sys
libs_dir = os.path.join(os.path.dirname( os.path.realpath( __file__ ) ),  '..', 'pythonlibs')
if os.path.isdir(libs_dir):                                       
    sys.path.append(libs_dir)
# Import the launcher and dbus modules
import launcher,dbus


# Define some values that will be used
my_signature = 'fi.hacklab.reactorsimulator.middleware'
launcher_config = {
    'dbus_default_interface_name': my_signature,
    'dbus_object_path': '/fi/hacklab/reactorsimulator/middleware/bridge',
    'main_class_name': os.path.basename(__file__).replace('_launcher.py', ''), 
    'config_file_path': os.path.realpath(__file__).replace('_launcher.py', '.yml'),
}

# Basic pass-through implementation
class my_launcher(launcher.baseclass):
    def __init__(self, mainloop, bus, **kwargs):
        super(my_launcher, self).__init__(mainloop, bus, **kwargs)
        print "launcher initialized as %s:%s with config %s" % (self.dbus_interface_name, self.dbus_object_path, repr(self.config))

    @dbus.service.method(my_signature + '.launcher')
    def quit(self):
        launcher.baseclass.quit(self)

    @dbus.service.method(my_signature + '.launcher')
    def reload(self):
        launcher.baseclass.reload(self)
        self.main_instance.config_reloaded()

# Another small bit of boilerplate
if __name__ == '__main__':
    launcher.main(my_launcher, **launcher_config)
