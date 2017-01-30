# Based on Andrew's LabelingTool_OneClick.py

import os, sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg
import numpy as np
from matplotlib.widgets import Button
import glob
from tempfile import TemporaryFile
import psycopg2
import pandas as pd
from os import listdir
from os.path import isfile, join
import urllib

class Annotate(object):
    def __init__(self, image,name, imgid):
    	self.zone = { 'imgid': None, 'location_x': None, 'location_y': None, 
    				  'zone': '0000', 'agg_zone': '0000' } 
    	self.zone['imgid'] = imgid
        self.img = image
        self.imgname = name
        self.imgid = imgid
        self.i = 1
        self.col = 'b' # deafult color for true positive label
        self.ax = plt.gca()
        # Initialize the Reactangle patch object with properties 
        self.rect = Rectangle((0,0), 1, 1, alpha = 1,ls = 'solid',fill = False, clip_on = True,color = self.col)
        # Initialize two diagonally opposite co-ordinates of reactangle as None
        self.xc = None
        self.yc = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.sizeModifier = 2
        
        self.w = 30.0
        self.h = 40.0
        self.qkey = None

        #self.centers
        # The list that will store value of those two co-ordinates of 
        # all the patches for storing into the file later
        self.xy = []
        self.ax.add_patch(self.rect)
        # Initialize mpl connect object 
        connect = self.ax.figure.canvas.mpl_connect
        # Create objects that will handle user initiated events 
        # We are using three events 
        # First event is button press event (on left key click)- 
        # on which on_click function is called
        connect('button_press_event', self.on_click)
        connect('close_event', self.handle_close)
        
        # Second event to draw, in case a mistake in labelling is made, 
        # deleting the patch requires redrawing the original canvas
        self.draw_cid = connect('draw_event', self.grab_background)
        
        # Third event - key press event
        # To change color of the patches when you want to switch between 
        # true postive and false postive labels
        connect('key_press_event',self.colorChange)
 



    def objCreation(self):
        # The new reactangle object to use after blit function (clearing 
        # the canvas and removing rectangle objects)
        
        self.rect = Rectangle((0,0), 1, 1, alpha = 1,ls = 'solid',fill = False, clip_on = True)
        self.xc = None # x co-ordinate of patch center
        self.yc = None # y co-ordinate of patch center
        self.x0 = None # top left x co-ordinate of patch center
        self.y0 = None # top left y co-ordinate of patch center
        self.x1 = None # lower right x co-ordinate of patch center
        self.y1 = None # lower right y co-ordinate of patch center
        self.sizeModifier = 2 # The amount by which width/height will increase/decrease
        self.w = 30.0 # Initial width
        self.h = 40.0 # Initial height
        # Aspect Ratio of 3/4
        # Add the patch on the axes object of figure
        self.ax.add_patch(self.rect)  


    def deletePrevious(self):
        '''
        Deletes the latest patch that was drawn
        '''
        # Clear the screen by calling blit function
        self.blit()
        # Remove the last patch co-ordinates from the list
        self.xy = self.xy[:-1]
        # Redraw all the rects except the previous ones
        for coords in self.xy:
            self.rect.set_width(coords[2] - coords[0])
            self.rect.set_height(coords[3] - coords[1])
            self.rect.set_xy((coords[0], coords[1]))
            self.rect.set_color(coords[4])
            self.ax.draw_artist(self.rect)
            self.ax.figure.canvas.blit(self.ax.bbox)

    def resize(self,det):
        '''
        Resizing at the same center, maintaing the same aspect ratio
        and using key only (without dragging)
        '''
        # Resizing without dragging requires deleting previous patch
        # Saving the center, width, height of the patch before deleting it
        # As it will be used for reconstructing with increased/decreased size
        last_obj = self.xy[-1]
        # print last_obj
        xc = last_obj[-2]
        yc = last_obj[-1]
        col = last_obj[-3]
        w = last_obj[2] - last_obj[0]
        h = last_obj[3] - last_obj[1]

        self.deletePrevious()
        self.xc = xc
        self.yc = yc
        self.col = col
        self.w = w*det 
        print self.w
        self.h =  h*det
        self.drawRect()

    def colorChange(self,event):
        '''
        To change color to take  false positves into consideration - the default is color blue for true postive
        '''
        print('press', event.key)
        sys.stdout.flush()
        if event.key == 'r': # red color
            # When 'r' key is pressed, the color of the next patch will be red
            self.col = 'r'
        elif event.key == 'b': # blue color
            # When 'b' key is pressed, the color of the next patch will be blue
            self.col = 'b' 

        elif event.key == 'd': # delete
            # When 'd' key is pressed, the latest patch drawn is deleted
            self.deletePrevious()

        elif event.key == 'c': # clear 
            # When 'c' key is pressed, all the patches are cleared, only orignal background is present
            self.blit()    
            self.xy = []
            # Flush out the list as we don't want to consider any patch co-ordinates

        elif event.key == 'tab':
            # use tab to increase the aspect ratio of the patch 

            self.resize(1.2)

        elif event.key == 'control':
            # use control key to decrease the aspect ratio of the patch
            self.resize(0.95)

        elif event.key == '2':
            # use control key to decrease the aspect ratio of the patch
            self.resize(0.85)

        elif event.key == '3':
            # use control key to decrease the aspect ratio of the patch
            self.resize(0.50)  

        elif event.key == 'q': # quit plot, show up the next
            # save necessary labels and close the plot
            self.qkey = 'q'
            self.close_plot()
                
        elif event.key == '0':
            sys.exit()
            


    def handle_close(self,event):
        '''
        if you ended up closing the plot using the plot's X button instead of 'q' key
        '''
        if self.qkey != 'q':
            self.close_plot()
    
    def close_plot(self):
        '''
        saving numpy patches and co-ordinates of the patches 
        '''
        if self.zone['location_x'] == None:
            self.zone['location_x'], self.zone['location_y'] = [None], [None]
            df = pd.DataFrame.from_dict(self.zone)
            with open('pic_1_500_location.csv', 'a') as f:
                df.to_csv(f, header=False)
        print 'close'
 
    def on_click(self, event):

        #print 'click1'
        self.xc = event.xdata
        self.yc = event.ydata
        # Chosing Aspect Ratio of 3/4
        self.w = 30.0
        self.h = 40.0
        self.xy.append([self.xc,self.yc])
        self.zone['location_x'] = [self.xc]
        self.zone['location_y'] = [self.yc]
        print self.zone['location_x'][0], self.zone['location_y'][0]
  
        img_center_x = (self.xmax+self.xmin)/2.0
        img_center_y = (self.ymax+self.ymin)/2.0

        binZone = int(self.zone['agg_zone'], 2)

        if self.zone['location_x'][0] > img_center_x:
            if self.zone['location_y'][0] > img_center_y:
                self.zone['zone'] = '0001'
                self.zone['agg_zone'] = "{0:b}".format(binZone|1)
            elif self.zone['location_y'][0] <= img_center_y:
                self.zone['zone'] = '1000'
                self.zone['agg_zone'] = "{0:b}".format(binZone|8)
        elif self.zone['location_x'][0] <= img_center_x:
            if self.zone['location_y'][0] > img_center_y:
                self.zone['zone'] = '0010'
                self.zone['agg_zone'] = "{0:b}".format(binZone|2)
            elif self.zone['location_y'][0] <= img_center_y:
                self.zone['zone'] = '0100'
                self.zone['agg_zone'] = "{0:b}".format(binZone|4)

        self.zone['agg_zone'] = self.zone['agg_zone'].zfill(4)
        print self.zone['zone']
        #print self.zone['agg_zone']
        
        df = pd.DataFrame.from_dict(self.zone)
        with open('pic_1_500_location.csv', 'a') as f:
        	df.to_csv(f, header=False)



       

    def drawRect(self):
        # Set the two diagonally opposite co-ordinates of the patch  by width and height
        self.x0 = self.xc-self.w/2
        self.y0 = self.yc-self.h/2
        self.x1 = self.xc+self.w/2
        self.y1 = self.yc+self.h/2
        # set the stated width
        self.rect.set_width(self.w)
        # set the stated height 
        self.rect.set_height(self.h)
        # set the top left corner
        self.rect.set_xy((self.x0, self.y0 )) 
        # Set the color of the reactangle - can be blue/red depending on postive/negative label respectively
        self.rect.set_color(self.col)
        self.ax.draw_artist(self.rect)
        # Blit is used to successively retain and display patches on the screen 
        # Else Successively drawing one patch will remove the last drawn patch 
        self.ax.figure.canvas.blit(self.ax.bbox)

    # The following three functions taken from 
    # http://stackoverflow.com/questions/29277080/efficient-matplotlib-redrawing

    def safe_draw(self):
        """Temporarily disconnect the draw_event callback to avoid recursion"""
        canvas = self.ax.figure.canvas
        canvas.mpl_disconnect(self.draw_cid)
        canvas.draw()
        self.draw_cid = canvas.mpl_connect('draw_event', self.grab_background)


    def grab_background(self, event=None):
        """
        When the figure is resized, hide the rect, draw everything,
        and update the background.
        """
        self.rect.set_visible(False)
        self.safe_draw()

        # With most backends (e.g. TkAgg), we could grab (and refresh, in
        # self.blit) self.ax.bbox instead of self.fig.bbox, but Qt4Agg, and
        # some others, requires us to update the _full_ canvas, instead.
        #self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.figure.bbox)
        self.rect.set_visible(True)
        # self.blit()

    def blit(self):
        """
        Efficiently update the figure, without needing to redraw the
        "background" artists.
        """
        self.objCreation()
        self.ax.figure.canvas.restore_region(self.background)
        self.ax.draw_artist(self.rect)
        self.ax.figure.canvas.blit(self.ax.figure.bbox)


# open files
data = pd.read_csv('finalLabels5146.csv')
base = 'https://streetopedia.com/static/'
params = '.jpg?height=480&width=640&zoom=1.6&heading=88.708230345076&pitch=4.0582547001702%22'
for ids in data.head(500)['id']:
    imgname = str(ids) + ".jpg"
    if isfile(imgname) == False:
        urllib.urlretrieve(base+str(ids)+params, str(ids)+".jpg")
    print ids
    
    imgid = ids

    img = mpimg.imread(imgname)

    # Create the canvas
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # print type(img)
    ax.imshow(img)

    ave_y = (ax.get_ylim()[0]+ax.get_ylim()[1])/2.0
    ave_x = (ax.get_xlim()[0]+ax.get_xlim()[1])/2.0
    ax.axhline(y = ave_y)
    ax.axvline(x = ave_x)

    a = Annotate(img, imgname, imgid)
    a.zone['imgid'] = a.imgid
    a.xmin, a.xmax, a.ymin, a.ymax = ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[1], ax.get_ylim()[0]
    plt.show()


if os.path.isfile("./pic_1_500_location.csv"):
    df = pd.read_csv("./pic_1_500_location.csv",header=None)
    df.rename(columns={1:"Zone", 2:"ID"}, inplace=True)
    df = df.loc[:,["ID","Zone"]]
    df.Zone = df.Zone.map(lambda x: str(x).zfill(4))
    df.drop_duplicates(subset=['ID'], keep='last', inplace=True)
    df.reset_index(drop = True, inplace = True)
    df.to_csv("pic_1_500_location.csv")