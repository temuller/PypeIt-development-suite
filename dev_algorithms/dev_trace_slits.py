from __future__ import (print_function, absolute_import, division, unicode_literals)

import numpy as np
from astropy.io import fits
import glob

from pypit import msgs
from pypit import ardebug as debugger
from pypit import ginga
from pypit import arload
from pypit import arproc
from pypit import arcomb
from pypit import ardeimos
from pypit import arlris

debug = debugger.init()
debug['develop'] = True
msgs.reset(debug=debug, verbosity=2)

from pypit import artrace

def_settings=dict(trace={'slits': {'single': [],
                                   'function': 'legendre',
                                   'polyorder': 3,
                                   'diffpolyorder': 2,
                                   'fracignore': 0.01,
                                   'medrep': 0,
                                   'number': -1,
                                   'maxgap': None,
                                   'sigdetect': 20.,
                                   'pca': {'params': [3,2,1,0,0,0], 'type': 'pixel', 'extrapolate': {'pos': 0, 'neg':0}},
                                   'sobel': {'mode': 'nearest'}},
                         'combine': {'match': -1.,
                                     'satpix': 'reject',
                                     'method': 'weightmean',
                                     'reject': {'cosmics': 20., 'lowhigh': [0,0], 'level': [3.,3.], 'replace': 'maxnonsat'}}})

def pypit_trace_slits():
    pass

def combine_frames(spectrograph, files, det, settings, saturation=None, numamplifiers=None):
    # Grab data info
    datasec, oscansec, naxis0, naxis1 = arproc.get_datasec(spectrograph, files[0],
                                                           numamplifiers=numamplifiers, det=det)

    # Load + process images
    frames = []
    for ifile in files:
        rawframe, head0 = arload.load_raw_frame(spectrograph, ifile, pargs.det, disp_dir=0)
        # Bias subtract
        newframe = arproc.sub_overscan(rawframe.copy(), numamplifiers, datasec, oscansec)
        # Trim
        frame = arproc.trim(newframe, numamplifiers, datasec)
        # Append
        frames.append(frame)

    # Convert to array
    frames_arr = np.zeros((frames[0].shape[0], frames[0].shape[1], len(frames)))
    for ii in range(len(frames)):
        frames_arr[:,:,ii] = frames[ii]

    # Combine
    mstrace = arcomb.comb_frames(frames_arr, frametype='Unknown',
                                 method=settings['trace']['combine']['method'],
                                 reject=settings['trace']['combine']['reject'],
                                 satpix=None, saturation=saturation)
    # Return
    return mstrace

def parser(options=None):
    import argparse
    # Parse
    parser = argparse.ArgumentParser(description='Developing/testing/checking trace_slits [v1.1]')
    parser.add_argument("instr", type=str, help="Instrument [keck_deimos, keck_lris_red]")
    parser.add_argument("--det", default=1, type=int, help="Detector")
    parser.add_argument("--show", default=False, action="store_true", help="Show the image with traces")
    parser.add_argument("--driver", default=False, action="store_true", help="Show the image with traces")

    if options is None:
        pargs = parser.parse_args()
    else:
        pargs = parser.parse_args(options)
    return pargs


def main(pargs):

    xgap = 0.0   # Gap between the square detector pixels (expressed as a fraction of the x pixel size)
    ygap = 0.0   # Gap between the square detector pixels (expressed as a fraction of the x pixel size)
    ysize = 1.0  # The size of a pixel in the y-direction as a multiple of the x pixel size
    binbpx = None
    numamplifiers = None
    saturation = None

    settings = def_settings.copy()
    if pargs.instr == 'keck_deimos':
        spectrograph = 'keck_deimos'
        saturation = 65535.0              # The detector Saturation level
        files = glob.glob('data/DEIMOS/DE*')
        #files = ['../RAW_DATA/Keck_DEIMOS/830G_L/'+ifile for ifile in ['d0914_0014.fits', 'd0914_0015.fits']]
        numamplifiers=1

        # Bad pixel mask (important!!)
        binbpx = ardeimos.bpm(pargs.det)

        #hdul = fits.open('trace_slit.fits')
        settings['trace']['slits']['sigdetect'] = 50.0
        settings['trace']['slits']['fracignore'] = 0.02
        settings['trace']['slits']['pca']['params'] = [3,2,1,0]
    elif pargs.instr == 'keck_lris_red':
        spectrograph = 'keck_lris_red'
        saturation = 65535.0              # The detector Saturation level
        files = glob.glob('data/LRIS/Trace_flats/r15*')
        numamplifiers=2

        settings['trace']['slits']['sigdetect'] = 50.0
        settings['trace']['slits']['pca']['params'] = [3,2,1,0]
    elif pargs.instr == 'keck_lris_blue':
        spectrograph = 'keck_lris_blue'
        saturation = 65535.0              # The detector Saturation level
        numamplifiers=2
        files = glob.glob('../RAW_DATA/Keck_LRIS_blue/long_600_4000_d560/b150910_2051*') # Single Twilight
    else:
        debugger.set_trace()

    # Combine
    mstrace = combine_frames(spectrograph, files, pargs.det, settings,
                             saturation=saturation, numamplifiers=numamplifiers)

    # binpx
    if binbpx is None:
        binbpx = np.zeros_like(mstrace)

    # pixlocn
    pixlocn = artrace.gen_pixloc(mstrace, xgap, ygap, ysize)

    # Trace
    if not pargs.driver:
        lcenint, rcenint, extrapord = artrace.refactor_trace_slits(pargs.det, mstrace, binbpx, pixlocn,
                                                               settings=settings, pcadesc="", maskBadRows=False, min_sqm=30.)
    else:
        lcenint, rcenint, extrapord = artrace.driver_trace_slits(pargs.det, mstrace, binbpx, pixlocn,
                                                                 settings=settings)
    if pargs.show:
        viewer, ch = ginga.show_image(mstrace)
        nslit = lcenint.shape[1]
        ginga.show_slits(viewer, ch, lcenint, rcenint, np.arange(nslit) + 1, pstep=50)

    debugger.set_trace()

if __name__ == '__main__':
    pargs = parser()
    main(pargs)
