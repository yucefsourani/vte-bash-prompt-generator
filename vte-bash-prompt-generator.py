#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  vte-bash-prompt-generator.py
#  
#  Copyright 2018 youcef sourani <youssef.m.sourani@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
# 
import os
import pwd
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk
import subprocess

COLORS={
        "reset"        :"\\033[0m" ,
        "black"        :"\\033[30m",
        "red"          :"\\033[31m",
        "green"        :"\\033[32m",
        "yellow"       :"\\033[33m",
        "blue"         :"\\033[34m",
        "magenta"      :"\\033[35m",
        "cyan"         :"\\033[36m",
        "light_gray"   :"\\033[37m",
        "dark_gray"    :"\\033[90m",
        "light_red"    :"\\033[91m",
        "light_green"  :"\\033[92m",
        "light_yellow" :"\\033[93m",
        "light_blue"   :"\\033[94m",
        "light_magenta":"\\033[95m",
        "light_cyan"   :"\\033[96m",
        "white"        :"\\033[97m"
        }
        
        
        
BG_COLORS={
        "reset"        :"\\033[0m"  ,
        "black"        :"\\033[40m" ,
        "red"          :"\\033[41m" ,
        "green"        :"\\033[42m" ,
        "yellow"       :"\\033[43m" ,
        "blue"         :"\\033[44m" ,
        "magenta"      :"\\033[45m" ,
        "cyan"         :"\\033[46m" ,
        "light_gray"   :"\\033[47m" ,
        "dark_gray"    :"\\033[100m",
        "light_red"    :"\\033[101m",
        "light_green"  :"\\033[102m",
        "light_yellow" :"\\033[103m",
        "light_blue"   :"\\033[104m",
        "light_magenta":"\\033[105m",
        "light_cyan"   :"\\033[106m",
        "white"        :"\\033[107m"
        
        }

OPTIONS1 = {"User Name"              :"\\u",
            "Host Name"              :"\\h",
            "FQDN"                   :"\\H",
            "Shell"                  :"\\s",
            "Shell Version"          :"\\v",
            "Shell Release"          :"\\V",
            "Full Current Directory" :"\\w ",
            "Current Directory"      :"\\W ",
            "$"                      :"\\$"
            }
            
OPTIONS2 = {"Date"                   :"\\d",
            "Time 24hr"              :"\\A",
            "Time 12hr"              :"\\@",
            "Time 24hr with Seconds" :"\\t",
            "Time 24hr with Seconds" :"\\T",
            "@"                      :"@",
            ":"                      :":",
            "["                      :"[",
            "]"                      :"]",
            "-"                      :"-",
            "_"                      :"_",
            "*"                      :"*"
           }

class CursorShape(Gtk.Dialog):
    def __init__(self,parent,terminal,t):
        Gtk.Dialog.__init__(self,parent=parent)
        self.set_modal(True)
        self.set_title("Cursor Shape") #cursor_shape
        
        self.t      = t
        self.parent = parent
        self.terminal = terminal
        parent_size = self.parent.get_size()
        width  = parent_size[0]
        height = parent_size[1]
        self.set_default_size(width/2 if width>600 else 300, height/2 if height>400 else 200)
        self.add_button("_OK", Gtk.ResponseType.OK)
        self.connect("response", self.on_response)

        label = Gtk.Label("Change Cursor Shape")
        self.vbox.pack_start(label,True,True,0)


        radiobutton1 = Gtk.RadioButton(label="Block")
        self.vbox.pack_start(radiobutton1, True, True, 0)
        
        radiobutton2 = Gtk.RadioButton(label="Ibeam ", group=radiobutton1)
        
        self.vbox.pack_start(radiobutton2, True, True, 0)
        
        radiobutton3 = Gtk.RadioButton(label="Under Line", group=radiobutton1)
        self.vbox.pack_start(radiobutton3, True, True, 0)
        
        if self.terminal.get_cursor_shape()==0:
            radiobutton1.set_active(True)
        elif self.terminal.get_cursor_shape()==1:
            radiobutton2.set_active(True)
        else:
            radiobutton3.set_active(True)
            
        radiobutton1.connect("toggled", self.on_radio_button_toggled,0)
        radiobutton2.connect("toggled", self.on_radio_button_toggled,1)
        radiobutton3.connect("toggled", self.on_radio_button_toggled,2)
        
        self.show_all()

    def on_radio_button_toggled(self,b,data):
        self.t[0] = data
        self.terminal.set_cursor_shape(Vte.CursorShape(data))
        
        
    def on_response(self, dialog, response):
        dialog.destroy()


class FontChange(Gtk.FontChooserDialog):
    def __init__(self,parent,terminal,t):
        Gtk.FontChooserDialog.__init__(self,parent=parent)
        self.set_title("FontChooserDialog")
        self.terminal = terminal
        self.t        = t
        
        response = self.run()
        if response == Gtk.ResponseType.OK:
            if self.t:
                self.t[0] = self.get_font_desc()
            else:
                self.t.append(self.get_font_desc())
            self.terminal.set_font(self.get_font_desc())
        
        self.destroy()
    

        
class Terminal(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Vte Bash Prompt Generator")
        self.maximize()
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.current = ""
        mainscrolledwindow = Gtk.ScrolledWindow()
        self.mainbox = Gtk.HBox(spacing=10)
        mainscrolledwindow.add(self.mainbox)
        self.tbox = Gtk.VBox(spacing=10)
        
        ####################################
        self.bg_color    = Gdk.RGBA(red=0.180392, green=0.203922, blue=0.211765, alpha=1.000000)
        self.fontsize    = []
        self.cursorshape = [0]
        self.cursorcolor = Gdk.RGBA(red=1.000000, green=1.000000, blue=1.000000, alpha=1.000000)
        #self.foreground  = Gdk.RGBA(red=1.000000, green=1.000000, blue=1.000000, alpha=1.000000)
        
        ####################################
        
        self.add(mainscrolledwindow)
        
        fbox1    = Gtk.HBox()
        flowbox1 = Gtk.FlowBox()
        flowbox1.props.homogeneous=True
        flowbox1.set_valign(Gtk.Align.START)
        flowbox1.set_max_children_per_line(1)
        flowbox1.set_selection_mode(Gtk.SelectionMode.NONE)
        fbox1.pack_start(flowbox1,False,False,0)
        self.mainbox.pack_start(fbox1,False,False,0)
        
        self.mainbox.pack_start(self.tbox ,True,True,0)
        
        fbox2    = Gtk.HBox()
        flowbox2 = Gtk.FlowBox()
        flowbox2.props.homogeneous=True
        flowbox2.set_valign(Gtk.Align.START)
        flowbox2.set_max_children_per_line(1)
        flowbox2.set_selection_mode(Gtk.SelectionMode.NONE)
        fbox2.pack_start(flowbox2,False,False,0)
        self.mainbox.pack_start(fbox2,False,False,0)
        
        flowbox3 = Gtk.FlowBox()
        flowbox3.props.homogeneous=True
        flowbox3.set_valign(Gtk.Align.START)
        flowbox3.set_max_children_per_line(1)
        flowbox3.set_selection_mode(Gtk.SelectionMode.NONE)
        fbox1.pack_start(flowbox3,False,False,0)

        flowbox4 = Gtk.FlowBox()
        flowbox4.props.homogeneous=True
        flowbox4.set_valign(Gtk.Align.START)
        flowbox4.set_max_children_per_line(1)
        flowbox4.set_selection_mode(Gtk.SelectionMode.NONE)
        fbox2.pack_start(flowbox4,False,False,0)
        
        for k,v in COLORS.items():
            b = Gtk.Button(k)
            b.connect("clicked",self.color_bg__button_clicked,v)
            flowbox1.add(b)
            

        for k,v in BG_COLORS.items():
            b = Gtk.Button("bg {}".format(k))
            b.connect("clicked",self.color_bg__button_clicked,v)
            flowbox2.add(b)
            
        for k,v in OPTIONS1.items():
            b = Gtk.Button(k)
            b.connect("clicked",self.color_bg__button_clicked,v)
            flowbox3.add(b)
            
        for k,v in OPTIONS2.items():
            b = Gtk.Button(k)
            b.connect("clicked",self.color_bg__button_clicked,v)
            flowbox4.add(b)
        

        
        self.entry        = Gtk.Entry()
        self.entry.props.placeholder_text="Enter PS1..."
        self.entry_buffer = self.entry.get_buffer()
        self.tbox.pack_start(self.entry,False,False,0)
        self.entry.connect("notify::text",self.on_entry_text_changed)
        self.entry.props.margin = 10
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition(0),"edit-copy")
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition(1),"edit-clear")
        #self.entry.set_icon_from_gicon(Gtk.EntryIconPosition(1),Gio.ThemedIcon(name="applications-multimedia"))
        self.entry.set_icon_tooltip_markup(Gtk.EntryIconPosition(0),"Copy")
        self.entry.connect("icon-press",self.on_copy_pressed)
 
 
        self.menu = Gtk.Menu()
        self.menu.set_screen(Gdk.Screen().get_default())
        

        fontsizemenuitem = Gtk.MenuItem("Font")
        cursorshapemenuitem = Gtk.MenuItem("Cursor Shape")
        cursorcolormenuitem = Gtk.MenuItem("Cursor Color")
        backgroundmenuitem = Gtk.MenuItem("Backgound Color")
        #foregroundmenuitem = Gtk.MenuItem("Foreground Color")
        
        fontsizemenuitem.connect("activate", self.font_change)
        cursorshapemenuitem.connect("activate", self.cursor_shape)
        cursorcolormenuitem.connect("activate", self.on_cursor_menuitem_activated)
        backgroundmenuitem.connect("activate", self.on_background_menuitem_activated)
        #foregroundmenuitem.connect("activate", self.on_foreground_menuitem_activated)
        
        self.menu.append(fontsizemenuitem)
        self.menu.append(cursorshapemenuitem)
        self.menu.append(cursorcolormenuitem)
        self.menu.append(backgroundmenuitem)
        #self.menu.append(foregroundmenuitem)


        self.terminal_gui()

    def on_copy_pressed(self,entry,icon_position,event):
        text = entry.get_text()
        if icon_position==0:
            if text:
                self.clipboard.set_text(text, -1)
        else:
            if text:
                self.entry_buffer.delete_text(self.entry.get_position()-1,1)
        
    def color_bg__button_clicked(self,button,color):
        self.entry_buffer.insert_text(self.entry.get_position(), color, len(color))
        self.entry.set_position(-1)
        self.entry.grab_focus_without_selecting()
        
        
    def terminal_gui(self,current=None):
        
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.terminal = Vte.Terminal()
        #self.terminal.set_sensitive(False)
        self.tbox.pack_start(self.scrolledwindow ,True,True,0)
        
        self.terminal.connect("eof",self.quit_)
        self.terminal.connect("current-directory-uri-changed",self.on_current_directory_uri_changed)
        self.terminal.set_cursor_shape(Vte.CursorShape(self.cursorshape[0]))
        self.terminal.set_color_background(self.bg_color)
        self.terminal.set_color_cursor(self.cursorcolor)
        #self.terminal.set_color_foreground(self.foreground)
        if self.fontsize:
            self.terminal.set_font(self.fontsize[0])
        self.terminal.set_allow_hyperlink(True)
        vadjustment = self.terminal.get_vadjustment()
        self.scrolledwindow.set_vadjustment(vadjustment)

        self.user_info = pwd.getpwuid(os.geteuid())
        text = self.entry.props.text
        
        if current:
            current_dir = current
        else:
            current_dir = self.user_info.pw_dir
        if text:
            t = subprocess.check_output("export PS1=\"{}\";echo $PS1".format(text),shell=True).decode("utf-8")[:-1]
            self.terminal.spawn_sync(
                            Vte.PtyFlags.DEFAULT,
                            current_dir,
                            ["/usr/bin/bash"],
                            ["export","PS1={}".format(t)],
                            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                            None,
                            None
                            )
        else:
            self.terminal.spawn_sync(
                            Vte.PtyFlags.DEFAULT,
                            current_dir,
                            ["/usr/bin/bash"],
                            [],
                            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                            None,
                            None
                            )
        

        self.scrolledwindow.add(self.terminal)
        self.terminal.connect("button-release-event",self.on_button_event)
        self.show_all()
        
    def on_entry_text_changed(self,entry,text):
        self.scrolledwindow.remove(self.terminal)
        self.tbox.remove(self.scrolledwindow)
        self.scrolledwindow.destroy()
        self.terminal.destroy()
        self.entry.set_sensitive(False)


        if self.current:
            self.entry.set_sensitive(True)
            self.entry.grab_focus_without_selecting()
            self.terminal_gui(self.current)
        else:
            self.terminal_gui()
            self.entry.set_sensitive(True)
            self.entry.grab_focus_without_selecting()

    def on_current_directory_uri_changed(self,terminal):
        try:
            self.current = "/".join(terminal.get_current_directory_uri().split("/")[3:])
            self.current = "/"+self.current
        except Exception as e:
            print(e)
            pass
            
    def font_change(self,w):
        FontChange(self,self.terminal,self.fontsize)
        
    def cursor_shape(self,w):
        CursorShape(self,self.terminal,t=self.cursorshape)
        
        
    def on_button_event(self,terminal,event):
        if  event.button==3:
            self.menu.popup_at_pointer()
            self.menu.show_all()

    def on_cursor_menuitem_activated(self,menuitem):
        colorchooserdialog = Gtk.ColorChooserDialog(parent=self)
        if colorchooserdialog.run() == Gtk.ResponseType.OK:
            color = colorchooserdialog.get_rgba()
            self.terminal.set_color_cursor(color)
            self.cursorcolor = color
        colorchooserdialog.destroy()
        
        
    def on_background_menuitem_activated(self,menuitem):
        colorchooserdialog = Gtk.ColorChooserDialog(parent=self)
        if colorchooserdialog.run() == Gtk.ResponseType.OK:
            color = colorchooserdialog.get_rgba()
            self.terminal.set_color_background(color)
            self.bg_color = color
        colorchooserdialog.destroy()

    def on_foreground_menuitem_activated(self,menuitem):
        colorchooserdialog = Gtk.ColorChooserDialog(parent=self)
        if colorchooserdialog.run() == Gtk.ResponseType.OK:
            color = colorchooserdialog.get_rgba()
            self.terminal.set_color_foreground(color)
            self.foreground = color
        colorchooserdialog.destroy()

    def quit_(self,w):
        Gtk.main_quit()
        
terminal = Terminal()
terminal.connect("delete-event", Gtk.main_quit)
terminal.show_all()
Gtk.main()
