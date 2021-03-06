#!/usr/bin/env python

import sys, usb, time

try:
    mpg=0
    while 1:
        dev = None
        print 'start'
        while dev == None:
            time.sleep(2)
            dev = usb.core.find(idVendor=0x03eb, idProduct=0x3110)
        print 'ok'
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

        print dev
        endpoint = dev[0][(0,0)][0]
        print "EP: %s" %endpoint
        
        while 1:    
         try:    
            data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize,
                            timeout=3000)
            print "data: "
            print time.time()
            print data
            
            
         except usb.core.USBError as e:
            print str(e)
            if e.errno != 110: # 110 is a timeout.
             print ("Error readin data: %s" % str(e))
             usb.util.dispose_resources(dev)
             break


except KeyboardInterrupt:
    raise SystemExit
        

