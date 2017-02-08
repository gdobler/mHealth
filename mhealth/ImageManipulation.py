'''
image manipulation
'''
from os import listdir
from os.path import isfile, join
import numpy as np
import scipy as sp
import scipy.ndimage as ndi


'''
public vars
'''
np.random.seed(200)
n_copy = 5
path = os.getcwd()+'\\input_img' #input_img is a folder containing cropped images
# color balance
cb_mean = 1
cb_std = 0.1
# gamma correction
contrast_threshold = 0.4
low_contrast_multipliers = np.random.uniform(contrast_threshold,1,n_copy)
high_contrast_multipliers = np.random.uniform(1,1/contrast_threshold,n_copy)
# resolution
resolution_multipliers = np.random.normal(0,2,n_copy)
# focus
focus_multipliers = np.random.normal(0,1,n_copy)


def main():
    inputs = [f for f in listdir(path) if isfile(join(path, f))]
    for i in range(len(inputs)):
        img = Im(inputs[i])
        img.generate_color_balance()
        img.generate_contrast()
        img.generate_resolution()
        img.generate_focus()


class Im(object):
    '''
    class image
    '''
    def __init__(self, filename):
        self.image = ndi.imread(join(path, filename))
        self.name = filename[:-4]

    def generate_color_balance(self):
        self.im2 = np.dstack([self.image[:,:,j].astype(float)/255 for j in range(3)])
        for n in range(n_copy):
            self.cb_multiplier = np.random.normal(cb_mean, cb_std, 3)
            self.imcb = (self.im2 * self.cb_multiplier).clip(0,1)
            sp.misc.imsave('./tmp/'+ self.name + '-cb-' +str(n)+'.png', self.imcb)
    
    def generate_contrast(self):
        self.contrast_multipliers = np.hstack([low_contrast_multipliers,high_contrast_multipliers])
        for n in range(len(self.contrast_multipliers)):
            self.con_multiplier = self.contrast_multipliers[n]
            self.imgsq = self.image.astype(float)**self.con_multiplier
            self.imgsq *= 255 / self.imgsq.max()
            self.imlc = self.imgsq.astype(np.uint8)
            sp.misc.imsave('./tmp/'+ self.name + '-con-' +str(n)+'.png', self.imlc)

    def generate_resolution(self):
        for n in range(n_copy):
            self.res_multiplier = np.absolute(resolution_multipliers[n])
            self.imlr = ndi.filters.uniform_filter(self.image, [self.res_multiplier,self.res_multiplier,0])
            sp.misc.imsave('./tmp/'+ self.name + '-res-' +str(n)+'.png', self.imlr)
    
    def generate_focus(self):
        for n in range(n_copy):
            self.foc_multiplier = np.absolute(focus_multipliers[n])
            self.imlf = ndi.filters.gaussian_filter(self.image, [self.foc_multiplier,self.foc_multiplier,0])
            sp.misc.imsave('./tmp/'+ self.name + '-foc-' +str(n)+'.png', self.imlf)


if __name__ == '__main__':
    main()
