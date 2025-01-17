""" Run the wavelength calibration routine on a set of
standard input spectra.  Generate summary output.
"""
from __future__ import (print_function, absolute_import, division, unicode_literals)

from pathlib import Path
import time
import glob
import astropy.io.fits as pyfits
import numpy as np
import warnings
import pdb
from matplotlib import pyplot as plt

from pypeit.core.wavecal import autoid

test_arc_path = str(Path().absolute()) + '/TEST_DATA/'
outdir = 'OUTPUT/'


def tst_thar(name, specs, wav_id, pix_id, test='general', toler=0.001):
    """
    toler : float
      Tolerance for scoring correct matches
    """
    # Favored parameters (should match those in the defaults)
    min_ampl = 200.
    lines = ['ThAr']

    # Run
    outroot = outdir+name
    if test == 'general':
        arcfitter = autoid.General(specs, lines, min_ampl=min_ampl,
                                   outroot=outroot, rms_threshold=0.15)
        patt_dict, final_fit = arcfitter.get_results()
        if patt_dict is None:
            return "FAILED", None, None
    else:
        pdb.set_trace()

    # Score
    grade = 'PASSED'
    slit = '0'
    nfail = 0
    for pp in range(pix_id.size):
        wid = np.argmin(np.abs(pix_id[pp]-final_fit[slit]['xfit']))
        if np.abs(wav_id[pp]-final_fit[slit]['yfit'][wid]) > toler:
            nfail += 1
    if nfail != 0:
        grade = "FAILED"
    # Warn
    warnings.warn("Solution for {:s} failed {:d}/{:d} lines".format(name, nfail, pix_id.size))
    return grade, patt_dict, final_fit


def main(flg_tst):

    if flg_tst in [1]:
        test = 'semi_brute'
    elif flg_tst in [2]:
        test = 'general'
    elif flg_tst in [3]:
        test = 'kdtree'
    else:
        pdb.set_trace()

    # Initialize
    names = []
    specs = []
    wavid = []
    pixid = []
    if True:
        # Test all HIREDUX solutions
        files = glob.glob(test_arc_path + "HIREDUX/*aspec.fits.gz")
        for fn in files:
            names += [fn.split("/")[-1]]
            filename = pyfits.open(fn)
            fx = filename[0].data
            ids = pyfits.open(fn.replace("aspec.fits.gz", "lines.fits.gz"))
            pxs = ids[1].data["PIX"]
            wvs = ids[1].data["WV"]
            ordflxs = None
            ordwavs, ordpixs = [], []
            for ord in range(fx.shape[0]):
                # Store the spectrum
                # ordspec += [fx[ord, :]]
                # Store the 'true' line IDs
                ww = np.where(wvs[ord, :] != 0.0)
                if np.all(fx[ord, :]) == 0.0:# or len(ww[0]) == 0:
                    continue
                else:
                    if ordflxs is None:
                        ordflxs = fx[ord, :].flatten().reshape((fx.shape[1], 1))
                    else:
                        ordflxs = np.append(ordflxs, fx[ord, :].flatten().reshape((fx.shape[1], 1)), axis=1)
                ordwavs += [wvs[ord, ww[0]]]
                ordpixs += [pxs[ord, ww[0]]]
                if len(specs) == 0:
                    coeff = np.polyfit(pxs[ord, ww[0]], wvs[ord, ww[0]], 4)
                    centwv = np.polyval(coeff, 0.5*fx.shape[1])
                    print("Central wavelength order {0:d}, pixel {1:d} = {2:f}".format(ord+1, fx.shape[1]//2, centwv))
            # specs += [ordspec]
            specs += [ordflxs]
            wavid += [ordwavs]
            pixid += [ordpixs]

    # Run it
    sv_grade = []  # for the end, just in case
    for name, spec, wvid, pxid in zip(names, specs, wavid, pixid):
        grades = np.zeros(len(spec), dtype=np.int)
        bwave, bdisp = np.zeros(len(spec)), np.zeros(len(spec))
        timstart = time.time()
        grade, patt_dict, final_fit = tst_thar(name, spec, wvid, pxid, test=test)
        for ord in range(spec.shape[1]):
            bwave[ord] = patt_dict[str(ord)]['bwv']
            bdisp[ord] = patt_dict[str(ord)]['bdisp']
            if grade == 'PASSED':
                grades[ord] = 1
        timfinish = time.time()
        sv_grade.append(grades.copy())
        pdb.set_trace()
        print("Completion time (minutes):", (timfinish-timstart)/60.0)
        plt.plot(bwave, bdisp, 'bo')
        plt.show()

    # Report it
    print('==============================================================')
    for name, grade in zip(names, sv_grade):
        print("{:s} :: PASSED {:d}/{:d}".format(name, np.sum(grade), grade.size))


# Test
if __name__ == '__main__':
    # flg_tst = 1   # Run em all with semi-brute
    flg_tst = 2   # Run em all with general

    main(flg_tst)
