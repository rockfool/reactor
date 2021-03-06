#!/usr/bin/env python
import os,sys,random
import dbus, gobject

class cell(dbus.service.Object):
    def __init__(self, rod, depth):
        self.rod = rod
        self.reactor = self.rod.reactor
        self.simulation_instance = self.reactor.simulation_instance
        self.x = self.rod.x
        self.y = self.rod.y
        self.depth = depth
        self.object_path = "%s/cell/%d" % (self.rod.object_path, self.depth)
        self.bus_name = dbus.service.BusName("fi.hacklab.reactorsimulator.engine.reactor.rod.x%d.y%d.cell.z%d" % (self.x, self.y, depth), bus=self.simulation_instance.bus)
        dbus.service.Object.__init__(self, self.bus_name, self.object_path)
        
        self.config_reloaded()

        self.rod = rod
        self.neutrons_seen = 0
        
        self.temp = float(self.config['ambient_temp']) # Celcius ?
        self.blend_temp = 0.0
        self.melted = False
        self.melt_warning_active = False

        # Final debug statement
        print "%s initialized" % self.object_path

    @dbus.service.method('fi.hacklab.reactorsimulator.engine')
    def decay(self):
        """This is the time-based decay, it will be called by a timer in the reactor"""
        # Rod position is checked in the neutron_hit method
        if random.random() > self.config['decay_p']:
            return
        self.neutron_hit()

    def unload(self):
        self.remove_from_connection()

    def config_reloaded(self):
        self.config = self.simulation_instance.config['cell']
        self.simulation_config = self.simulation_instance.config['simulation']
        self.neutron_hit_p = [[[ self.config['neutron_hit_p'] for val in range(self.config['neutron_grid_size'])] for col in range(self.config['neutron_grid_size'])] for row in range(self.config['neutron_grid_size'])]
        # TODO: Calculate center from the grid size
        self.neutron_hit_p[1][1][1] = 0.0 # We're in the center, easiest way is to set p to zero

    @dbus.service.method('fi.hacklab.reactorsimulator.engine')
    def cool(self, cool_by=None):
        """This is the time-based cooling, it will be called by a timer in the reactor"""
        if not cool_by:
            self.temp -= self.config['cool_temp_decrease']
        else:
            self.temp -= cool_by
        if self.temp < self.config['ambient_temp']:
            self.temp = self.config['ambient_temp']
        #print "DEBUG: %s cool(), temp %f" % (self.object_path, self.temp)

    def calc_blend_temp(self):
        """Calculates next blend_temp"""
        self.blend_temp = 0.0
        cell_count = 0
        for xdelta in range(self.simulation_config['blend_grid_size']):
            for ydelta in range(self.simulation_config['blend_grid_size']):
                for zdelta in range(self.simulation_config['blend_grid_size']):
                    # TODO: Calculate center (the "1" contstant below) from the grid size
                    x = self.x + (xdelta - 1)
                    y = self.y + (ydelta - 1)
                    z = self.depth + (zdelta - 1)
                    if not self.reactor.in_grid(x,y,z):
                        #print "DEBUG blend [%d,%d,%d] is outside the grid" % (x,y,z)
                        continue
                    if not self.reactor.layout[x][y]:
                        #print "DEBUG blend [%d,%d] has no rod" % (x,y)
                        # Nothing there
                        continue
                    try:
                        n_temp = self.reactor.layout[x][y].cells[z].temp
                    except:
                        try:
                            n_temp = self.reactor.layout[x][y].temperatures[z] # blend the measurement wells too
                        except:
                            pass
                    self.blend_temp += n_temp # Sum neighbouring cell temps
                    cell_count += 1

        if not cell_count:
            self.blend_temp = self.temp
            return
        self.blend_temp /= cell_count # and average them
        self.blend_temp = (1.0 - self.simulation_config['temperature_blend_weight']) * self.temp + (self.simulation_config['temperature_blend_weight'] * self.blend_temp)

    def sync_blend_temp(self):
        """sync the buffered blend_temps to cell real temp"""
        self.temp = float(self.blend_temp)
        #print "DEBUG: %s sync_blend_temp(), temp %f" % (self.object_path, self.temp)

    @dbus.service.method('fi.hacklab.reactorsimulator.engine')
    def neutron_hit(self):
        """This is where most of the magic happens, whenever we have a split atom we generate heat and with some P trigger hits in neighbours"""
        self.neutrons_seen += 1 # keep track of the flow

        # If the moderator is past this point it will always absorb the hits, nothing will happen
        if (self.rod.moderator_depth >= self.depth):
            return
        
        self.temp += self.config['neutron_hit_temp_increase']

        #print "DEBUG: %s neutron_hit(), temp %f" % (self.object_path, self.temp)

        for xdelta in range(self.config['neutron_grid_size']):
            for ydelta in range(self.config['neutron_grid_size']):
                for zdelta in range(self.config['neutron_grid_size']):
                    # TODO: Calculate center (the "1" contstant below) from the grid size
                    x = self.x + (xdelta - 1)
                    y = self.y + (ydelta - 1)
                    z = self.depth + (zdelta - 1)
                    if not self.reactor.in_grid(x,y,z):
                        continue
                    hit_p = float(self.neutron_hit_p[xdelta][ydelta][zdelta])
                    # The graphite tip is at our place, accelerate reaction
                    if (self.rod.tip_depth == z):
                        hit_p += self.config['tip_neutron_hit_p_increase']
#                    if (self.rod.moderator_depth >= self.depth):
#                        hit_p = self.config['rod_inplace_neutron_hit_p']
                    if random.random() > hit_p:
                        # No hit
                        continue
                    if not self.reactor.layout[x][y]:
                        # Nothing to hit
                        continue
                    try:
                        # I guess these should be marshalled through mainloops event system
                        #self.reactor.layout[x][y].neutron_hit(z)
                        gobject.idle_add(self.reactor.layout[x][y].neutron_hit, z)
                    except:
                        # Skip errors
                        pass

        pass

if __name__ == '__main__':
    print "Use simulationengine.py"
    sys.exit(1)
