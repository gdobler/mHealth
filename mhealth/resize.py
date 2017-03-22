
import pandas as pd
import numpy as np
import re
from scipy import misc
import matplotlib.pyplot as plt
import scipy
from PIL import Image


csv_dir = "./pitch643.csv"
raw_dir = "./raw/"
pitch_dir = "./png/"


class img(object):
    def __init__(self, pitch_name):
        self._glob_size = None # (Height, Width)
        self._glob_ratio = None # Height / Width
        self._local_size = None # (Height, Width)
        self._local_ratio = None # Height / Width

        self._zoom_rate = 1.1
        self._local_resize = None # (Height, Width)

        self._local_center = None # (y-axis/height, x-axis/width)
        self._box = {
                    'top': None,
                    'bottom': None,
                    'left': None,
                    'right': None
                    }

        self._csv_dir = csv_dir
        self._raw_dir = raw_dir
        self._pitch_dir = pitch_dir

        self._pitch_name = pitch_name
        self._imgid = int(pitch_name.split("_")[0])
        self._imgname = str(pitch_name.split("_")[0])+'.jpg'

        self._raw_img = None
        self._pitch = None
        self._pitch_resize = None
        self._pitch_glob_size = None

    def connect(self, csv, raw):
        if not self._csv_dir:
            self._csv_dir = csv
        if not self._raw_dir:
            self._raw_dir = raw 

    def PitchInfo(self):
        info = pd.read_csv(self._csv_dir)
        info['Center'] = info['Center'].map(lambda a: (float(re.findall("[0-9.]+",a)[0]), float(re.findall("[0-9.]+",a)[1])))
        # Global Size
        self._glob_size = (max(info['Height']), max(info['Width']))
        self._glob_ratio = 1.0 * self._glob_size[0] / self._glob_size[1]
        # Local Size
        img_info = info[info['Name'] == self._pitch_name].to_dict()
        self._local_size = (img_info['Height'].values()[0], img_info['Width'].values()[0])
        self._local_ratio = 1.0 * self._local_size[0] / self._local_size[1]
        # Center
        c = img_info['Center'].values()[0]
        self._local_center = (float(c[1]), float(c[0])) # (y-axis, x-axis)

    def new_local_size(self):
        pitch = misc.imread(pitch_dir + self._pitch_name + '.png')
        self._pitch = pitch
        raw = misc.imread(raw_dir + self._imgname)
        self._raw_img = raw
        raw = np.asarray(raw)

        h, w = float(self._local_size[0]), float(self._local_size[1])
        rate = self._zoom_rate
        center = self._local_center

        if self._local_ratio < self._glob_ratio:
            h_new = w * (1.0 * self._glob_ratio) * rate
            w_new = w 
        elif self._local_ratio > self._glob_ratio:
            h_new = h 
            w_new = h * (1.0 / self._glob_ratio) * rate
        else:
            h_new = h 
            w_new = w 
        self._local_resize = (h_new, w_new)

        self._box['top'] = max(0.0, center[0] - 1.0 * h_new / 2)
        self._box['bottom'] = min(float(raw.shape[0]), center[0] + 1.0 * h_new / 2)
        self._box['left'] = max(0.0, center[1] - 1.0 * w_new / 2) 
        self._box['right'] = min(float(raw.shape[1]), center[1] + 1.0 * w_new / 2)

        if self._box['top'] == 0:
            self._box['bottom'] = h_new - 1
        if self._box['bottom'] == float(raw.shape[0]):
            self._box['top'] = float(raw.shape[0]) - h_new +1
        if self._box['left'] == 0:
            self._box['right'] = w_new - 1
        if self._box['right'] == float(raw.shape[1]):
            self._box['left'] = float(raw.shape[1]) - w_new +1
        
        self._pitch_resize = raw[self._box['top']:self._box['bottom']+1, self._box['left']:self._box['right']+1]

    def zoom(self):
        pitch = Image.fromarray(self._pitch_resize)
        if self._local_ratio <= self._glob_ratio:
            basewidth = self._glob_size[1]
            wpercent = (basewidth / float(pitch.size[0]))
            hsize = int((float(pitch.size[1])*float(wpercent)))
            pitch2 = pitch.resize((int(basewidth),int(hsize)), Image.ANTIALIAS)
        elif self._local_ratio > self._glob_ratio:
            baseheight = self._glob_size[0]
            hpercent = (baseheight / float(pitch.size[1]))
            wsize = int((float(pitch.size[0])*float(hpercent)))
            pitch2 = pitch.resize((int(wsize),int(baseheight)), Image.ANTIALIAS)
        else:
            print "Warning"

        pitch2 = np.asarray(pitch2)   
        h_start = int((pitch2.shape[0] - self._glob_size[0])/2)
        w_start = int((pitch2.shape[1] - self._glob_size[1])/2)
        
        if self._local_ratio < self._glob_ratio:
            # pitch2 = pitch2[h_start : (h_start + int(np.ceil(self._glob_size[0]))), :int(np.ceil(self._glob_size[1]))]
            pitch2 = pitch2[h_start : (h_start + int(np.ceil(self._glob_size[0]))), :]
        elif self._local_ratio > self._glob_ratio:
            # pitch2 = pitch2[:int(np.ceil(self._glob_size[0])), w_start : (w_start + int(np.ceil(self._glob_size[1])))]
            pitch2 = pitch2[:, w_start : (w_start + int(np.ceil(self._glob_size[1])))]
        self._pitch_glob_size = np.asarray(pitch2)

    def run(self):
        self.PitchInfo()
        self.new_local_size()
        self.zoom()

    def info(self):
        print "Image ID {}\n".format(self._pitch_name)
        print "Global:\nsize: {}\nratio(h/w): {}".format(self._glob_size, self._glob_ratio)
        print "Local:\nsize: {}\nratio(h/w): {}".format(self._local_size, self._local_ratio)
        print "Global : Local = {}".format(1.0 * self._glob_size[0] / self._local_size[0])
        print "Box(resize) = {}".format(self._box)
        print "Shape:\nraw: {}\npitch: {}\npitch resize: {}\npitch gloab size: {}".format(self._pitch.shape, self._pitch.shape, self._pitch_resize.shape, self._pitch_glob_size.shape)

    def output(self):
        if self._pitch_glob_size.shape[:2] != self._glob_size:
            print self._local_resize
            print self._pitch_name, self._pitch_glob_size.shape[:2], self._glob_size
            print self._box
            print self._local_ratio > self._glob_ratio
        #plt.imsave("./res/rs_png/" + str(self._pitch_name), self._pitch_resize)
        plt.imsave("./res/gs_png/" + str(self._pitch_name), self._pitch_glob_size)
        #np.save("./res/rs_npy/" + str(self._pitch_name) + ".npy", self._pitch_resize)
        np.save("./res/gs_npy/" + str(self._pitch_name) + ".npy", self._pitch_glob_size)


def main():
    pitch = pd.read_csv(csv_dir)
    pNames = pitch['Name']
    for i, p in enumerate(pNames):
        a = img(p)
        a.run()
        a.output()  
        print "\r{} %".format(100.0*(i+1)/len(pNames)),
    print "Done!"


if __name__ == '__main__':
    main()

