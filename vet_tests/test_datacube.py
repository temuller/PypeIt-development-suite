"""
Module to run tests on arcoadd
"""
import os

import pytest

from pypeit.core.datacube import coadd_cube
from pypeit.spectrographs.util import load_spectrograph
from pypeit import inputfiles
from astropy.table import Table

from IPython import embed

import warnings
warnings.simplefilter("ignore", UserWarning)

def test_coadd_datacube(redux_out):
    """ Test the coaddition of spec2D files into datacubes """
    droot = os.path.join(redux_out,
                         'keck_kcwi', 
                         'bh2_4200', 
                         'Science')
    files = [os.path.join(droot,
                          'spec2d_KB.20191219.56886-BB1245p4238_KCWI_20191219T154806.538.fits'),
             os.path.join(droot,
                          'spec2d_KB.20191219.57662-BB1245p4238_KCWI_20191219T160102.755.fits')]
    output_filename = "BB1245p4238_KCWI_20191219.fits"
    # Generate a dummy CubeFile
    data = Table()
    data['filename'] = files
    confdict = {'rdx': {'spectrograph': 'keck_kcwi'}}
    cubeFile = inputfiles.CubeFile(data_table=data, config=confdict)
    # Get some options
    opts = [cubeFile.cube_opts(None)]*len(files)
    # Grab the spectrograph and parset
    spec = load_spectrograph("keck_kcwi")
    parset = spec.default_pypeit_par()
    parset['reduce']['cube']['output_filename'] = output_filename
    parset['reduce']['cube']['combine'] = True
    parset['reduce']['cube']['astrometric'] = False
    parset['reduce']['cube']['grating_corr'] = False
    coadd_cube(files, opts, parset=parset, overwrite=True)
    # Now test the fluxing
    flux_files = [files[0]]
    output_fileflux = "BB1245p4238_KCWI_20191219_fluxing.fits"
    parset['reduce']['cube']['output_filename'] = output_fileflux
    parset['reduce']['cube']['combine'] = False
    parset['reduce']['cube']['standard_cube'] = output_filename
    parset['reduce']['cube']['astrometric'] = False
    parset['reduce']['cube']['grating_corr'] = False
    coadd_cube(flux_files, opts, parset=parset, overwrite=True)
    # Check the files exist
    assert(os.path.exists(output_filename))
    assert(os.path.exists(output_fileflux))
    # Remove the created files
    os.remove(output_filename)
    os.remove(output_fileflux)