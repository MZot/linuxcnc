#!/usr/bin/env python
# GladeVcp Widget - tooledit
#
# Copyright (c) 2012 Chris Morley
# Modified 2016 Jim Craig <jimcraig5615  at  windstream dot  net>
# Modified 2017 Mit Zot 
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

#simulacija tipkovnice - :
#Installing the module uinput
#Make sure that you have the python pip installer installed this will make it easier to build an install on your Linux system.
#    sudo apt-get install  python-pip
#Then to install the module using the python pip installer.
#   sudo pip install python-uinput --index-url=https://pypi.python.org/simple
#If all the prerequisites are satisfied this will download compile and install the python module. :)
#The module requires Uinput kernel module to be running this can easily be done with
#   sudo modprobe uinput
#This will load the module this time round. I you want it to load every time you reboot your system then it will need to be added to the /etc/modules file. To edit the file from your command line.
#   sudo nano /etc/modules
#Add an extra time to the line to the file with.
#   uinput
#Then.
#   Ctrl + x
#This will save and exit just hit  Y to confirm overwriting the file.
##rule for uinput
#sudo nano /lib/udev/rules.d/50-udev-default.rules
#dodaj KERNEL=="uinput", GROUP="cnc"


import sys, os, pango, linuxcnc, hashlib, glib, uinput
sys.path.insert(0,'..')
import simpleeval
datadir = os.path.abspath(os.path.dirname(__file__))
KEYWORDS = ['S','T', 'P', 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'D', 'I', 'J', 'Q', ';']
try:
    import gobject,gtk
except:
    print('GTK not available')
    sys.exit(1)

# localization
import locale
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
LOCALEDIR = os.path.join(BASE, "share", "locale")
locale.setlocale(locale.LC_ALL, '')

# we put this in a try so there is no error in the glade editor
# linuxcnc is probably not running then
try:
    INIPATH = os.environ['INI_FILE_NAME']
except:
    INIPATH = None

class Tooledit(gtk.VBox):
    __gtype_name__ = 'Tooledit'
    __gproperties__ = {
        'font' : ( gobject.TYPE_STRING, 'Pango Font', 'Display font to use',
                "sans 12", gobject.PARAM_READWRITE|gobject.PARAM_CONSTRUCT),
        'hide_columns' : (gobject.TYPE_STRING, 'Hidden Columns', 'A no-spaces list of columns to hide: stpxyzabcuvwdijq and ; are the options',
                    "", gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
        'lathe_display_type' : ( gobject.TYPE_BOOLEAN, 'Display Type', 'True: Lathe layout, False standard layout',
                    False, gobject.PARAM_READWRITE | gobject.PARAM_CONSTRUCT),
    }
    __gproperties = __gproperties__

    def __init__(self,toolfile=None, *a, **kw):
        super(Tooledit, self).__init__()
        self.emcstat = linuxcnc.stat()
        self.hash_check = None 
        self.lathe_display_type = True
        self.toolfile = toolfile
        self.num_of_col = 1
        self.font="sans 16"
        self.hide_columns =''
        self.toolinfo_num = 0
        self.toolinfo = []
        self.wTree = gtk.Builder()
        self.wTree.set_translation_domain("linuxcnc") # for locale translations
        self.wTree.add_from_file(os.path.join(datadir, "tooledit_gtk.glade") )
        # connect the signals from Glade
        dic = {
            "on_delete_clicked" : self.delete,
            "on_add_clicked" : self.add,
            "on_reload_clicked" : self.reload,
            "on_save_clicked" : self.save,
            "cell_toggled" : self.toggled
            }
        self.wTree.connect_signals( dic )

        self.treeview1 = self.wTree.get_object("treeview1")
        self.treeview1.connect("key-release-event", self.on_tree_navigate_key_press, None)

        # for raw view 1:

        # toggle button useable
        renderer = self.wTree.get_object("cell_toggle1")
        renderer.set_property('activatable', True)
        # make colums editable
        self.tool_cell_list = "cell_tool#","cell_pos","cell_x","cell_y","cell_z","cell_a","cell_b","cell_c","cell_u","cell_v","cell_w","cell_d", \
                "cell_front","cell_back","cell_orient","cell_comments"
        for col,name in enumerate(self.tool_cell_list):
            #print name,col
            renderer = self.wTree.get_object(name+'1')
            renderer.connect( 'edited', self.col_editted, col+1, None)
            renderer.props.editable = True
        self.all_label = self.wTree.get_object("all_label")

        renderer = self.wTree.get_object('cell_tool#1')
        renderer.props.editable = False

        # for lathe wear view2:

        # make columns editable
        temp =[ ("cell_x2",3),("cell_z2",5),("cell_front2",13),("cell_back2",14), \
                ("cell_orient2",15), ("cell_comments2",16)]
        for name,col in temp:
            renderer = self.wTree.get_object(name)
            renderer.connect( 'edited', self.col_editted, col, 'wear' )
            renderer.props.editable = True
        # Hide columns we don't want to see
        self.set_col_visible(list='spyabcuvwdijq', bool= False, tab= '2')
        self.wear_label = self.wTree.get_object("wear_label")

        # for tool offsets view 3:

        # make columns editable
        temp =[ ("cell_x3",3),("cell_z3",5),("cell_front3",13),("cell_back3",14), \
                ("cell_orient3",15), ("cell_comments3",16)]
        for name,col in temp:
            renderer = self.wTree.get_object(name)
            renderer.connect( 'edited', self.col_editted, col, 'tool' )
            renderer.props.editable = True
        # Hide columns we don't want to see
        self.set_col_visible(list='spyabcuvwdij', bool= False, tab= '3')
        self.tool_label = self.wTree.get_object("tool_label")

        # global references
        self.model = self.wTree.get_object("liststore1")
        self.notebook = self.wTree.get_object("tool_offset_notebook")
        self.all_window = self.wTree.get_object("all_window")
        self.wear_window = self.wTree.get_object("wear_window")
        self.tool_window = self.wTree.get_object("tool_window")
        self.view1 = self.wTree.get_object("treeview1")
        self.view2 = self.wTree.get_object("treeview2")
        # sort routine for tool diameter
        def compare(model, row1, row2, user_data=None):
            sort_column, _ = model.get_sort_column_id()
            value1 = model.get_value(row1,sort_column)
            value2 = model.get_value(row2,sort_column)
            return cmp(value1,value2)
        model = self.view1.get_model()
        model.set_sort_func(12, compare)
        #self.view2.connect('button_press_event', self.on_treeview2_button_press_event)
        self.view2.connect("key-release-event", self.on_tree_navigate_key_press, 'wear')
        self.selection = self.view2.get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)
        self.view3 = self.wTree.get_object("treeview3")
        #self.view3.connect('button_press_event', self.on_treeview2_button_press_event)
        self.view3.connect("key-release-event", self.on_tree_navigate_key_press, 'tool')
        self.apply = self.wTree.get_object("apply")
        self.buttonbox = self.wTree.get_object("buttonbox")
        self.tool_filter = self.wTree.get_object("tool_modelfilter")
        self.tool_filter.set_visible_func(self.match_type,False)
        self.wear_filter = self.wTree.get_object("wear_modelfilter")
        self.wear_filter.set_visible_func(self.match_type,True)
        # reparent tooledit box from Glades tp level window to tooledit's VBox
        window = self.wTree.get_object("tooledit_box")
        window.reparent(self)
        # If the toolfile was specified when tooledit was created load it
        if toolfile:
            self.reload(None)
        # check the ini file if display-type: LATHE is set
        try:
            self.inifile = linuxcnc.ini(INIPATH)
            test = self.inifile.find("DISPLAY", "LATHE")
            if test == '1' or test == 'True':
                self.lathe_display_type = True
                self.set_lathe_display(True)
            else:
                self.lathe_display_type = False
                self.set_lathe_display(False)
        except:
            pass
        self.s = simpleeval.SimpleEval()
        # check linuxcnc status every second
        gobject.timeout_add(1000, self.periodic_check)
        self.keyboard =  uinput.Device((uinput.KEY_DOWN,uinput.KEY_END))

    # used to split tool and wear data by the tool number
    # if the tool number is above 10000 then its a wear offset (as per fanuc)
    # returning true will show the row
    def match_type(self, model, iter, data):
        value = model.get_value(iter, 1)
        if value < 10000:
            return not data
        return data


         # delete the selected tool
    def delete(self,path):
         #try: tle se neki ni ok
         iter = self.model.get_iter(path)
         self.model.remove(iter)
         glib.timeout_add(50, self.select_cell, self.view2, path, self.treeview1.get_columns()[3])
         #except:
         #pass            

        # return the selected tool number
    def get_selected_tool(self):
        path, col = self.treeview1.get_cursor()
        return (self.model[path][1], path)



    def set_selected_tool(self,toolnumber):
        try:
            treeselection = self.view2.get_selection()
            liststore  = self.model
            def match_tool(model, path, iter, pathlist):
                if model.get_value(iter, 1) == toolnumber:
                    pathlist.append(path)
                return False     # keep the foreach going
            pathlist = []
            liststore.foreach(match_tool, pathlist)
            # foreach works in a depth first fashion
            if len(pathlist) == 1:
                liststore.set_value(liststore.get_iter(pathlist[0]),0,1)
                treeselection.select_path(pathlist[0])
        except:
            print "tooledit_widget error: cannot select tool number",toolnumber



    def get_first_nonexisting_tool(self):
        liststore = self.model
        t = 0
        i=0
        toollist = []
        for row in liststore:
            toollist.append(int(row[1]))
            
        if len(toollist) == 0:
           return 1   
        else:
           try:
             return sorted(set(xrange(1, max(toollist))) - set(toollist))[0]
           except:
             return (max(toollist))+1

     

    def add(self,widget,data=[1,0,0,'0','0','0','0','0','0','0','0','0','0','0','0','0',""]):
       if data[0] and self.lathe_display_type: 
        try:
         data[1]=int(self.wTree.get_object("entry_tool_n").get_text())
         tool_orientation_radio_buttons = "radiobutton1","radiobutton2","radiobutton3","radiobutton4","radiobutton5","radiobutton6","radiobutton7","radiobutton8","radiobutton9"
         angles = (112,157),(22,67),(292,337),(202,247),(202,158),(68,112),(22,-22),(248,292),(0,0)
         for i,orient in enumerate(tool_orientation_radio_buttons):
            if self.wTree.get_object(orient).get_active():
              data[15]=i+1
              data[13] = angles[i][0]
              data[14] = angles[i][1]
        except:
           pass
       self.model.append(data)
       self.num_of_col +=1
       for row in range(len(self.model)): #selektira novo orodje
             if self.model[row][1] == data[1]:
               self.view1.set_cursor(row, None, False)
               self.view1.grab_focus()
               break

        # this is for adding a filename path after the tooleditor is already loaded.
    def set_filename(self,filename):
        self.toolfile = filename
        self.reload(None)

        # Reload the tool file into display
    def reload(self,widget):
        columns = [c for c in self.treeview1.get_columns()]
        try: #saves current cell and restores it at the end
          path, col = self.treeview1.get_cursor()
          colnum = columns.index(col)
        except:
          colnum = 3  #set focus on col X, first line in treeview at start
          path =(0,)  
        self.hash_code = self.md5sum(self.toolfile)
        # clear the current liststore, search the tool file, and add each tool
        if self.toolfile == None:return
        self.model.clear()
        #print "toolfile:",self.toolfile
        if not os.path.exists(self.toolfile):
            print "Toolfile does not exist"
            return
        logfile = open(self.toolfile, "r").readlines()
        self.toolinfo = []
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
                        if offset == 1:
                            if int(word.lstrip(i)) == self.toolinfo_num:
                                toolinfo_flag = True
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
            self.add(None,array)
        try:
         glib.timeout_add(50,
                            self.treeview1.set_cursor,
                            path, columns[colnum], True)
        except:
         pass 


        # Note we have to save the float info with a decimal even if the locale uses a comma        #strictly use dot as decimal separator, no matter what locale says - MZ
    def save(self,widget):
        if self.toolfile == None:return
        file = open(self.toolfile, "w")
        #print self.toolfile

        liststore = self.model
        sorted_model = gtk.TreeModelSort(liststore)
        sorted_model.set_sort_column_id(1, 0)

        liststore = sorted_model
        for row in liststore:
            values = [ value for value in row ]
            #print values
            line = ""
            for num,i in enumerate(values):
                if num == 0: continue
                elif num in (1,2): # tool# pocket#
                    line = line + "%s%d "%(KEYWORDS[num], i)
                elif num == 16: # comments
                    test = i.strip()
                    line = line + "%s%s "%(KEYWORDS[num],test)
                elif num==3 and self.lathe_display_type:  #lathe diameter on X
                    test = i.lstrip() # localized floats
                    line = line + "%s%s "%(KEYWORDS[num], locale.atof(test)/2.0)
                elif num == 12 and self.lathe_display_type:  #lathe tool nose radius, not diameter
                    test = i.lstrip() # localized floats
                    line = line + "%s%s "%(KEYWORDS[num], locale.atof(test)*2.0)
                else:
                    test = i.lstrip() # localized floats
                    line = line + "%s%s "%(KEYWORDS[num], locale.atof(test))

            print >>file,line
        # Theses lines are required to make sure the OS doesn't cache the data
        # That would make linuxcnc and the widget to be out of synch leading to odd errors
        file.flush()
        os.fsync(file.fileno())
        # tell linuxcnc we changed the tool table entries
        try:
            linuxcnc.command().load_tool_table()
        except:
            print "Reloading tooltable into linuxcnc failed"

        # This is for changing the display after tool editor was loaded using the style button
        # note that it toggles the display
    def display_toggle(self,widget=None):
        value = (self.display_type * -1) +1
        self.set_display(value)

        # There is an 'everything' display and a 'lathe' display
        # the same model is used in each case just the listview is different
        # does the actual display change by hiding what we don't want
        # for whatever reason I have to hide/show both the view and it's container
    def set_lathe_display(self,value):
        #print "    lathe_display    ",value
        self.lathe_display_type = value
        #if self.all_window.flags() & gtk.VISIBLE:
        self.notebook.set_show_tabs(False)
        if value:
            self.wear_window.show()
            self.view3.show()
            self.tool_window.show()
            self.view2.show()
            
            self.wTree.get_object('d1').set_title('R')
        else:
            self.view2.hide()
            self.wear_window.hide()
            
            self.tool_window.hide()
            self.view3.hide()

    def set_font(self, value, tab='123'):
        for i in range(0, len(tab)):
            if tab[i] in ('1','2','3'):
                for col,name in enumerate(self.tool_cell_list):
                    temp2 = self.wTree.get_object(name+tab[i])
                    temp2.set_property('font', value)
        self.set_title_font(value, tab)
        self.set_tab_font(value, tab)

    # set font of the column titles
    def set_title_font(self, value, tab='123'):
        objectlist = "s","t","p","x","y","z","a","b","c","u","v","w","d","i","j","q",";"
        for i in range(0, len(tab)):
            if tab[i] in ('1','2','3'):
                for j in objectlist:
                    column = self.wTree.get_object(j+tab[i])
                    label = gtk.Label(column.get_title())
                    label.modify_font(pango.FontDescription(value))
                    label.show()
                    column.set_widget(label)

    def set_tab_font (self, value, tab='123'):
        for i in range(0, len(tab)):
            if tab[i] in ('1','2','3'):
                if tab[i] =='1':
                    self.all_label.modify_font(pango.FontDescription(value))
                elif tab[i] =='2':
                    self.wear_label.modify_font(pango.FontDescription(value))
                elif tab[i] =='3':
                    self.tool_label.modify_font(pango.FontDescription(value))
                else:
                    pass

    # for legacy interface
    def set_visible(self,list,bool):
        self.set_col_visible(list, bool, tab= '1')

    # This allows hiding or showing columns from a text string of columnns
    # eg list ='xyz'
    # tab= selects what tabs to apply it to
    def set_col_visible(self, list, bool= False, tab= '1'):
        #print list,bool,tab
        for i in range(0, len(tab)):
            if tab[i] in ('1','2','3'):
                #print tab[i]
                for index in range(0, len(list)):
                    colstr = str(list[index])
                    #print colstr
                    colnum = 'stpxyzabcuvwdijq;'.index(colstr.lower())
                    #print colnum
                    name = KEYWORDS[colnum].lower()+tab[i]
                    #print name
                    renderer = self.wTree.get_object(name)
                    renderer.set_property('visible', bool)

    # For single click selection when in edit mode
    def on_treeview2_button_press_event(self, widget, event):
        if event.button == 1 : # left click
            try:
                path, model, x, y = widget.get_path_at_pos(int(event.x), int(event.y))
                widget.set_cursor(path, None, True)
            except:
                pass

        # depending what is editted add the right type of info integer,float or text
        # If it's a filtered display then we must convert the path 
    def col_editted(self, widget, path, new_text, col, filter):
        if filter == 'wear':
            (store_path,) = self.wear_filter.convert_path_to_child_path(path)
            path = store_path
        elif filter == 'tool':
            (store_path,) = self.tool_filter.convert_path_to_child_path(path)
            path = store_path
        
        if col in(1,2):
            try:
                self.model[path][col] = int(new_text).strip()
            except:
                pass
        elif col in range(3,12):
            try:
               self.model[path][col] = ("%10.03f " % self.s.eval(new_text)).lstrip() #locale.format("%10.4f",locale.atof(new_text))
            except:
                pass
        elif col == 12:
            try:
                self.model[path][col] = ("%10.3f" % self.s.eval(new_text)).strip() #("%10.2f" % self.s.eval(new_text)) #locale.format("%10.4f",locale.atof((new_text)))
            except:
                pass
        elif col in range(13,16):
            try:
                self.model[path][col] = ("%10.0f" % self.s.eval(new_text)).strip() #locale.format("%10.0f",locale.atof(new_text))
            except:
                pass
        elif col == 16:
            try:
                self.model[path][col] = (new_text)
            except:
                pass
        #print path,new_text, col
        if filter in('wear','tool'):
            self.save(None)

        # this makes the checkboxes actually update
    def toggled(self, widget, path):
        model = self.model
        model[path][0] = not model[path][0]

        # check for linnuxcnc ON and IDLE which is the only safe time to edit the tool file.
        # check to see if the tool file is current
    def periodic_check(self):
        try:
            self.emcstat.poll()
            on = self.emcstat.task_state > linuxcnc.STATE_OFF
            idle = self.emcstat.interp_state == linuxcnc.INTERP_IDLE
            self.apply.set_sensitive(bool(on and idle))
        except:
            pass
        if self.toolfile:
            self.file_current_check()
        return True

        # create a hash code
    def md5sum(self,filename):
        try:
            f = open(filename, "rb")
        except IOError:
            return None
        else:
            return hashlib.md5(f.read()).hexdigest()

        # check the hash code on the toolfile against
        # the saved hash code when last reloaded.
    def file_current_check(self):
        m = self.hash_code
        m1 = self.md5sum(self.toolfile)
        if m1 and m != m1:
            self.toolfile_stale()

        # you could overload this to do something else.
    def toolfile_stale(self):
        print "Tool file was modified since it was last read"
        self.reload(None)

        # Returns the tool information array of the requested toolnumber
        # or current tool if no tool number is specified
        # returns None if tool not found in table or if there is no current tool
    def get_toolinfo(self,toolnum=None):
        if toolnum == None:
            self.toolinfo_num = self.emcstat.tool_in_spindle
        else:
            self.toolinfo_num = toolnum
        self.reload(None)
        if self.toolinfo == []: return None
        return self.toolinfo

        # 'convenience' method to hide buttons
        # you must call this after show_all()
    def hide_buttonbox(self, data):
        if data:
            self.buttonbox.hide()
        else:
            self.buttonbox.show()

        # standard Gobject method
    def do_get_property(self, property):
        name = property.name.replace('-', '_')
        if name in self.__gproperties.keys():
            return getattr(self, name)
        else:
            raise AttributeError('unknown property %s' % property.name)

        # standard Gobject method
        # changing the Gobject property 'display_type' will actually change the display
        # This is so that in the Glade editor, you can change the display
        # Note this sets the display absolutely vrs the display_toggle method that toggles the display
    def do_set_property(self, property, value):
        name = property.name.replace('-', '_')
        if name == 'font':
            try:
                self.set_font(value)
            except:
                pass
        elif name == 'lathe_display_type':
            #print value
            if INIPATH is None:
                try:
                    self.set_lathe_display(value)
                except:
                    pass
        elif name == 'hide_columns':
            try:
                self.set_col_visible("sptxyzabcuvwdijq;", True)
                self.set_col_visible("%s" % value, False)
            except:
                pass



    # define the callback for keypress events
    cell_edited=False
    def on_tree_navigate_key_press(self, treeview, event, filter):
        keyname = gtk.gdk.keyval_name(event.keyval)
        path, col = treeview.get_cursor()
        columns = [c for c in treeview.get_columns()]
        colnum = columns.index(col)

        focuschild = treeview.focus_child

        if filter == 'wear':
            store_path = self.wear_filter.convert_path_to_child_path(path)
            path = store_path
        elif filter == 'tool':
            store_path = self.tool_filter.convert_path_to_child_path(path)
            path = store_path

        if keyname == 'Tab' or keyname == 'Right':
         if self.cell_edited == False: 
            cont = True
            cont2 = True
            i = 0
            while cont:
                i += 1
                if colnum + i < len(columns):
                    if columns[colnum + i].props.visible:
                        renderer = columns[colnum + i].get_cell_renderers()
                        if renderer[0].props.editable:
                            next_column = columns[colnum + i]
                            cont = False

                else:
                    i = 1
                    while cont2:
                        renderer = columns[i].get_cell_renderers()
                        if renderer[0].props.editable:
                            next_column = columns[len(columns)-1]  #i]
                            cont2 = False
                        else:
                            i += 1
                    cont = False

            if keyname == 'Right':
                renderer = columns[colnum].get_cell_renderers()
                if type(focuschild) is gtk.Entry:
                    self.col_editted(renderer[0], path, treeview.focus_child.props.text, colnum, filter)
            glib.timeout_add(50, self.select_cell,treeview,path, next_column)

        elif keyname == 'Left':
         if self.cell_edited == False: 
            cont = True
            cont2 = True
            i = 0
            while cont:
                i -= 1
                if colnum + i > 0:
                    if columns[colnum + i].props.visible:
                        renderer = columns[colnum + i].get_cell_renderers()
                        if renderer[0].props.editable:
                            next_column = columns[colnum + i]
                            cont = False

                else:
                    i = -1
                    while cont2:
                        renderer = columns[i].get_cell_renderers()
                        if renderer[0].props.editable:
                            next_column = columns[colnum]  #i]
                            cont2 = False
                        else:
                            i -= 1
                    cont = False

            renderer = columns[colnum].get_cell_renderers()
            if type(focuschild) is gtk.Entry:
                self.col_editted(renderer[0], path, treeview.focus_child.props.text, colnum, filter)
            glib.timeout_add(50, self.select_cell,treeview,path, next_column)

        elif keyname == 'Down':
            if self.cell_edited:
                self.cell_edited=False
                return
            model = treeview.get_model()
            # Check if currently in last row of Treeview
            if path[0] + 1 == len(model):
                path = (0, )
                # treeview.set_cursor(path, columns[colnum], True)
                glib.timeout_add(50, self.select_cell,treeview,path, columns[colnum])
            else:
                newpath = path[0] + 1
                # treeview.set_cursor(path, columns[colnum], True)
                glib.timeout_add(50, self.select_cell,treeview,newpath, columns[colnum])
            self.cell_edited = False 


        elif keyname == 'Up':
            if self.cell_edited:
                self.cell_edited=False
                return
            model = treeview.get_model()
            if path[0] == 0:
                newpath = len(model)-1
            else:
                newpath = path[0] - 1
            glib.timeout_add(50, self.select_cell,treeview,newpath, columns[colnum])

        elif keyname == 'Return' or keyname == 'KP_Enter':  #select cell for editing or accept changes
              renderer = columns[colnum].get_cell_renderers()
              #print 'return from tooledit'
              if self.cell_edited:
                self.cell_edited = False
                if type(focuschild) is gtk.Entry:
                   self.col_editted(renderer[0], path, treeview.focus_child.props.text, colnum, filter)         
              #else:
              #  glib.timeout_add(100, self.press_end)
              #  self.cell_edited = True

              glib.timeout_add(50, self.select_cell,treeview,path, columns[colnum])


        elif (keyname == 'Shift_R'): #select for editing
             if not self.cell_edited:
                glib.timeout_add(50, self.select_cell,treeview,path, columns[colnum])
                glib.timeout_add(150, self.press_end)
                self.cell_edited = True

        elif keyname == 'Escape':
                self.wTree.get_object("entry_tool_n").grab_focus()
                self.cell_edited = 0 
                glib.timeout_add(50, self.select_cell,treeview,path, columns[colnum])

        else:
            pass

    def press_end(self):
           self.keyboard.emit(uinput.KEY_END,1)
           self.keyboard.emit(uinput.KEY_END,0)

    def select_cell(self, treeview, path, column):
        try:
         treeview.set_cursor(path, column, True)
        except:
         pass


# for testing without glade editor:
# for what ever reason tooledit always shows both display lists,
# in the glade editor it shows only one at a time (as it should)
# you can specify a tool table file at the command line
# or uncomment the line and set the path correctly.
def main(filename=None):
    window = gtk.Dialog("My dialog",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    tooledit = Tooledit(filename)
    
    window.vbox.add(tooledit)
    window.connect("destroy", gtk.main_quit)
    tooledit.set_col_visible("abcUVW", False, tab='1')
    # uncommented the below line for testing.
    tooledit.set_filename("/home/jim/linuxcnc/configs/sim.gmoccapy/tool.tbl")
    #tooledit.set_filename("/home/chris/emc2-dev/configs/sim/lathe.tbl")
    tooledit.set_font("sans 16",tab='23')
    window.show_all()
    #tooledit.set_lathe_display(True)
    response = window.run()
    if response == gtk.RESPONSE_ACCEPT:
       print "True"
    else:
       print "False"

if __name__ == "__main__":
    # if there are two arguments then specify the path
    if len(sys.argv) > 1: main(sys.argv[1])
    else: main()
    
    
