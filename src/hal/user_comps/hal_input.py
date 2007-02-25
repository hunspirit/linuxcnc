import linux_event, sys, os, fcntl, hal, select, time, glob, fnmatch

class HalInputDevice:
    def __init__(self, comp, idx, name):
	self.device = linux_event.InputDevice(name)

	self.idx = idx
	self.drive = {}
	self.abs = {}
	self.last = {}
	self.comp = comp

	for key in self.device.get_bits('EV_KEY'):
	    key = str(key).lower()
	    comp.newpin("%s.%s" % (idx, key), hal.HAL_BIT, hal.HAL_OUT)
	    self.drive[key] = 0

	for axis in self.device.get_bits('EV_ABS'):
	    name = str(axis).lower()
	    self.abs[name] = self.device.get_absinfo(axis)
	    comp.newpin("%s.%s" % (idx, name), hal.HAL_FLOAT, hal.HAL_OUT)
	    self.drive[name] = 0

	for led in self.device.get_bits('EV_LED'):
	    name = str(led).lower()
	    comp.newpin("%s.%s" % (idx, name), hal.HAL_BIT, hal.HAL_IN)
	    self.last[name] = 0
	    self.device.write_event('EV_LED', led, 0)

    def update(self):
	while self.device.readable():
	    ev = self.device.read_event()
	    if ev.type == 'EV_KEY':
		code = str(ev.code).lower()
		if code not in self.drive:
		    print >>sys.stderr, "Unexpcted event EV_KEY", code, ev.code
		    continue
		if ev.value:
		    self.drive[code] = 1
		else:
		    self.drive[code] = 0
	    if ev.type == 'EV_ABS':
		code = str(ev.code).lower()
		if code not in self.drive:
		    print >>sys.stderr, "Unexpcted event EV_KEY", code, ev.code
		    continue
		absinfo = self.abs[code]
		if abs(ev.value) < absinfo.flat: ev.value = 0
		scale = max(-absinfo.minimum, absinfo.maximum)
		self.drive[code] = ev.value * 1. / scale

	for k, v in self.drive.items():
	    self.comp["%s.%s" % (self.idx, k)] = v

	for k, v in self.last.items():
	    u = self.comp["%s.%s" % (self.idx, k)]
	    if u != self.last[k]:
		self.device.write_event('EV_LED', k.upper(), u)
		self.last[k] = u

h = hal.component("input")
d = []
for i, f in enumerate(sys.argv[1:]):
    d.append(HalInputDevice(h, i, f))

try:
    while 1:
	time.sleep(.01)
	for i in d: i.update()
except KeyboardInterrupt:
    pass
