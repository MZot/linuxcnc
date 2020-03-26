#!/usr/bin/env python
#
#Widget for selecting tool
#
#Copyright (c) 2018 Mit Zot
#Uses some code from tooleditwidget by Chris Morley
#
#It shows treeview with tool data read from tooltable
#returns selected tool number
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.



try:
    import gobject,gtk
except:
    print('GTK not available')
    sys.exit(1)

import sys, os, pango, linuxcnc

KEYWORDS = ['S','T', 'P', 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'D', 'I', 'J', 'Q', ';']


class Toolselector():
    def __init__(self,toolfile=None, cols=KEYWORDS, lathe=False, *a, **kw):
        self.toolfile = toolfile
        self.lathe_display_type = lathe
        self.selected_tool=-1
        self.selected_row=0
        self.cols_visible = cols

        self.dialog = gtk.Dialog("Select tool to change to",
                    None,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.dialog.set_size_request(700, 240)
        
        self.listmodel = gtk.ListStore(str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str, str)
        self.treeview = gtk.TreeView(model=self.listmodel)
        self.treeview.connect('key-press-event', self.key_press) 
        for i, column in enumerate(KEYWORDS):
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_min_width(70)
            if column in self.cols_visible:
             col.set_visible(True)
            else:
             col.set_visible(False)
            self.treeview.append_column(col)

        self.reload()

        self.dialog.vbox.pack_start(self.treeview)
        self.treeview.show()

    def key_press(self, view, event):
        keyname = gtk.gdk.keyval_name( event.keyval )
        #print keyname
        if keyname == "Return":
           self.selected_tool = self.get_selected_tool()
           self.dialog.response(gtk.RESPONSE_OK)

    def show_dialog(self):
        response = self.dialog.run()
        self.dialog.hide()
        if response == gtk.RESPONSE_OK:
           return self.selected_tool
        else:
           return -1

        # return the selected tool number
    def get_selected_tool(self):
        path, col = self.treeview.get_cursor()
        self.selected_row = path[0]
        return (self.listmodel[path][1])


        # Reload the tool file into display
    def reload(self):
        if not os.path.exists(self.toolfile):
            print "Toolfile does not exist"
            return
        logfile = open(self.toolfile, "r").readlines()
        self.toolinfo = []
        self.listmodel.clear()
        for rawline in logfile:
            # strip the comments from line and add directly to array
            # if index = -1 the delimiter ; is missing - clear comments
            index = rawline.find(";")
            comment =''
            if not index == -1:
                comment = (rawline[index+1:])
                comment = comment.rstrip("\n")
                line = rawline.rstrip(comment)
            else:
                line = rawline       
            array = [0,0,0,'0','0','0','0','0','0','0','0','0','0','0','0','0',comment]
            toolinfo_flag = False
            # search beginning of each word for keyword letters
            # offset 0 is the checkbutton so ignore it
            # if i = ';' that is the comment and we have already added it
            # offset 1 and 2 are integers the rest floats
            # we strip leading and following spaces from the comments
            for offset,i in enumerate(KEYWORDS):
                if offset == 0 or i == ';': continue
                for word in line.split():
                    if word.startswith(';'): break
                    if word.startswith(i):
                        if offset in(1,2):
                            try:
                                array[offset]= int(word.lstrip(i))
                            except:
                                print "Tooledit widget int error"
                        elif offset == 12:
                             try: 
                                if self.lathe_display_type:  
                                    array[offset]= ("%10.02f " % (float(word.lstrip(i))/2) ).lstrip()      
                                else:                                       
                                    array[offset]= ("%10.02f" % float(word.lstrip(i))).strip() #locale.format("%10.4f", float(word.lstrip(i)))   #strictly use dot as decimal separator, no matter what locale says - MZ
                             except:
                                print "Tooledit_widget float error"
                        elif offset in(13, 14, 15):
                            try:
                                array[offset]= ("%10.0f" % float(word.lstrip(i))).strip()
                            except:
                                print "Tooledit widget int error"
                        elif offset == 3 and self.lathe_display_type:  #lathe diameter on X
                            try:                                                  
                                array[offset]= ("%10.03f " % (float(word.lstrip(i))*2) ).lstrip()
                            except:
                                print "Tooledit_widget float error"
                        elif offset == 12 and self.lathe_display_type:  #lathe tool nose radius, not diameter
                            try:                                                  
                                array[offset]= ("%10.03f " % (float(word.lstrip(i))/2) ).lstrip()
                            except:
                                print "Tooledit_widget float error"
                        else:
                            try:                                                  
                                array[offset]= ("%10.03f " % float(word.lstrip(i))).lstrip()
                            except:
                                print "Tooledit_widget float error"
                        break
            if toolinfo_flag:
                self.toolinfo = array
            # add array line to liststore
            self.listmodel.append(array)
        try:
          self.treeview.set_cursor(self.selected_row, None, False)
        except:
          pass


def main(filename=None):
    toolsel = Toolselector(filename, ['T', 'X', 'Y', 'Z', 'D', 'I', 'J', 'Q', ';'], False)
    print toolsel.show_dialog()
    


if __name__ == "__main__":
    # if there are two arguments then specify the path
    if len(sys.argv) > 1: main(sys.argv[1])
    else: main()




