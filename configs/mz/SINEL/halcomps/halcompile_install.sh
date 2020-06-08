#!/bin/sh



xfce4-terminal -x bash -c  'echo "Compiling and installing:"; \
                            . /home/cnc/LinuxCNC/linuxcnc/scripts/rip-environment ; \
                            find ./ -name "*.comp" -exec sh -c "echo ; 
                                                                echo -n {} ; 
                                                                echo ; 
                                                                halcompile --install {}" \; ; 
                            echo ; \
                            echo "done, check output for errors!" ; \
                            read ; '