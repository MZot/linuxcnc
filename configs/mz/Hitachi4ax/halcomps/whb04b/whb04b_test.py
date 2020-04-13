#!/usr/bin/env python

import sys, usb, time

try:
    mpg=0
    while 1:
        dev = None
        print 'start'
        while dev == None:
            time.sleep(2)
            dev = usb.core.find(idVendor=0x10ce, idProduct=0xeb93)
        
        try:
            if dev.is_kernel_driver_active(0) is True:
                dev.detach_kernel_driver(0)
        except usb.core.USBError as e:
            print("WHB04B: Kernel driver won't give up control over device: %s" % str(e))

        try:
            dev.set_configuration()
            dev.reset()
        except usb.core.USBError as e:
            print("WHB04B: Cannot set configuration the device: %s" % str(e))

        endpoint = dev[0][(0,0)][0]
        
        while 1:    
         try:    
            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize,
                            timeout=1000)
            print "axis selector: %i" %data[5]
            print "increment selector: %i" %data[4]
            print "first button: %i" %data[2]
            print "second button: %i" %data[3]
            if data[6] > 127:
             mpg=mpg+(256 - data[6])*-1
            else:
             mpg=mpg+data[6]
            print "MPG count: %i" %mpg
            
         except usb.core.USBError as e:
            print str(e)
            if e.errno != 110: # 110 is a timeout.
             print ("Error readin data: %s" % str(e))
             usb.util.dispose_resources(dev)
             break


except KeyboardInterrupt:
    raise SystemExit
        

