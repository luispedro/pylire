#!/usr/bin/env python
from __future__ import division

import numpy
import math

from pylire.process.grayscale import ITU_R_601_2

CANNY_THRESHOLD_LOW = 60.0
CANNY_THRESHOLD_HIGH = 100.0
PHOG_BINS = 30

PI_OVER_TWO = numpy.pi / 2.0
PI_OVER_EIGHT = numpy.pi / 8.0
THREE_PI_OVER_EIGHT = 3.0 * numpy.pi / 8.0

# Notes (from the Lire source):
# // used to quantize bins to [0, quantizationFactor]
# // Note that a quantization factor of 127d has better precision,
# but is not supported by the current serialization method.
QUANTIZATION_FACTOR = 15.0

# histogram_out = numpy.zeros(
#     PHOG_BINS + 4*PHOG_BINS + 4*4*PHOG_BINS,
#     dtype="uint8")
# histogram = numpy.zeros(
#     PHOG_BINS + 4*PHOG_BINS + 4*4*PHOG_BINS,
#     dtype="double")


def set_canny_pixel(x, y, grayscale, value):
    if value > CANNY_THRESHOLD_LOW:
        grayscale[x, y] = 0
    elif value > CANNY_THRESHOLD_HIGH:
        grayscale[x, y] = 128
    else:
        grayscale[x, y] = 255


def track_weak_ones(x, y, grayscale):
    """ Tail-recursive neighborhood-stalking function to hunt
        and normalize weak pixels (with extreme predjudice) """
    for xx in xrange(x - 1, x + 1):
        for yy in xrange(y - 1, y + 1):
            # 'if isWeak()' (unrolled)
            if 0 < grayscale[xx, yy] < 255:
                grayscale[xx, yy] = 0
                track_weak_ones(xx, yy, grayscale)


def naive_sobel(grayscale):
    """ Totally naive port of pixel-loop logic, taken straight
        from Lire's PHOG implementation:
    https://github.com/fish2000/lire/blob/master/src/main/java/net/semanticmetadata/lire/imageanalysis/PHOG.java#L288
        ... There are a bajillion better ways to Sobel things
        (including fast Python implementations in scipy,
        scikit-image, and mahotas) which will replace this
        torturously braindead semantic-wholesale-copy Java-style
        for-loop hodown... in THE FUTURE. """
    (W, H) = grayscale.shape[:2]
    sobelX = numpy.zeros((W, H), dtype="double")
    sobelY = numpy.zeros((W, H), dtype="double")
    # N.B. these loops start at 1, not zero
    for x in xrange(1, W - 1):
        for y in xrange(1, H - 1):
            sX = sY = 0
            sX += grayscale[x - 1, y - 1]
            sY += grayscale[x - 1, y - 1]
            sX += 2 * grayscale[x - 1, y]
            sX += grayscale[x - 1, y + 1]
            sY -= grayscale[x - 1, y + 1]
            
            sX -= grayscale[x + 1, y + 1]
            sY += grayscale[x + 1, y - 1]
            sX -= 2 * grayscale[x + 1, y]
            sX -= grayscale[x + 1, y + 1]
            sY -= grayscale[x + 1, y + 1]
            sobelX[x, y] = sX
            
            sY += 2 * grayscale[x, y - 1]
            sY -= 2 * grayscale[x, y + 1]
            sobelY[x, y] = sY
    return (sobelX, sobelY)

def PHOG(R, G, B):
    grayscale = ITU_R_601_2(R, G, B)
    (W, H) = grayscale.shape[:2]
    (sobelX, sobelY) = naive_sobel(grayscale)
    grayD = numpy.zeros((W, H), dtype="double")
    grayM = numpy.zeros((W, H), dtype="double")
    
    # "setting gradient magnitude and gradinet direction"
    for x in xrange(W):
        for y in xrange(H):
            if sobelX[x, y] != 0.0:
                grayD[x, y] = math.atan(sobelY[x, y] / sobelX[x, y])
            else:
                grayD[x, y] = PI_OVER_TWO
            grayM[x, y] = math.sqrt(sobelY[x, y]**2 + sobelX[x, y]**2)
    
    # "non-maximum suppression"
    grayscale[:, 0] = 255
    grayscale[:, H - 1] = 255
    grayscale[0, :] = 255
    grayscale[W - 1, :] = 255
    
    for x in xrange(1, W - 1):
        for y in xrange(1, H - 1):
            
            if grayD[x, y] < PI_OVER_EIGHT and grayD[x, y] >= -PI_OVER_EIGHT:
                if grayM[x, y] > grayM[x + 1, y] and grayM[x, y] > grayM[x - 1, y]:
                    set_canny_pixel(x, y, grayscale, grayM[x, y])
                else:
                    grayscale[x, y] = 255
            
            elif grayD[x, y] < THREE_PI_OVER_EIGHT and grayD[x, y] >= PI_OVER_EIGHT:
                if grayM[x, y] > grayM[x - 1, y - 1] and grayM[x, y] > grayM[x + 1, y + 1]:
                    set_canny_pixel(x, y, grayscale, grayM[x, y])
                else:
                    grayscale[x, y] = 255
    
            elif grayD[x, y] < -THREE_PI_OVER_EIGHT or grayD[x, y] >= THREE_PI_OVER_EIGHT:
                if grayM[x, y] > grayM[x, y + 1] and grayM[x, y] > grayM[x, y - 1]:
                    set_canny_pixel(x, y, grayscale, grayM[x, y])
                else:
                    grayscale[x, y] = 255
            
            elif grayD[x, y] < -PI_OVER_EIGHT and grayD[x, y] >= -THREE_PI_OVER_EIGHT:
                if grayM[x, y] > grayM[x + 1, y - 1] and grayM[x, y] > grayM[x - 1, y + 1]:
                    set_canny_pixel(x, y, grayscale, grayM[x, y])
                else:
                    grayscale[x, y] = 255
            
            else:
                grayscale[x, y] = 255
            
    
    # print(grayscale)
    # print("")
    # print("MAXIMUM GRAY: %s" % numpy.max(grayscale))
    # print("")
    # print("")
    
    # "hysteresis ... walk along lines of strong pixels and make the weak ones strong."
    for x in xrange(1, W - 1):
        for y in xrange(1, H - 1):
            # track_weak_ones() is tail-call recursive
            grayscale[x, y] < 50 and track_weak_ones(x, y, grayscale)
    
    # "removing the single weak pixels." -- as Frank Underwood says,
    # "Cleave them from the herd, and watch them die."
    for x in xrange(2, W - 2):
        for y in xrange(2, H - 2):
            if grayscale[x, y] > 50:
                grayscale[x, y] = 255
    
    
    


def main(pth):
    from pylire.compatibility.utils import test
    from pylire.process.channels import RGB
    from imread import imread
    
    (R, G, B) = RGB(imread(pth))
    
    @test
    def timetest_naive_PHOG(R, G, B):
        phog_histo = PHOG(R, G, B)
    
    timetest_naive_PHOG(R, G, B)

if __name__ == '__main__':
    
    from os.path import expanduser, basename, join
    from os import listdir
    
    im_directory = expanduser("~/Downloads")
    im_paths = map(
        lambda name: join(im_directory, name),
        filter(
            lambda name: name.lower().endswith('jpg'),
            listdir(im_directory)))
    
    for im_pth in im_paths:
        
        print("")
        print("")
        print("IMAGE: %s" % basename(im_pth))
        main(im_pth)


