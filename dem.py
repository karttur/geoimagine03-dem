'''
Created on 27 Mar 2021

@author: thomasgumbricht
'''

# Standard library imports

import os

from sys import exit

# Third party imports

from osgeo import gdal

from gdalconst import *

# Package application imports

from geoimagine.gis import GetRasterMetaData

from geoimagine.ktgdal import GDALinternal, GDALexternal

import geoimagine.support.karttur_dt as mj_dt

class ProcessDEM(GDALinternal, GDALexternal):
    '''class for processing DEM''' 
      
    def __init__(self, pp, session):
        '''
        '''
        
        self.session = session
                
        self.pp = pp  
        
        self.verbose = self.pp.process.verbose 
        
        self.session._SetVerbosity(self.verbose) 
        
        GDALinternal.__init__(self)   
        
        GDALexternal.__init__(self)      
        
        # Direct to subprocess
        if self.pp.process.processid == 'GdalDemRegion':
            
            self._GdalDemRegion()
            
        elif self.pp.process.processid == 'GdalDemTiles':
            
            self._GdalDemTiles()
            
        else:
        
            print (self.pp.process.processid)

            exit('DEM process not recognized in processDEM')
    
    def _GdalDemTiles(self):
        '''
        '''
        self.scriptFD = {}; self.scriptFPND = {}
          
        for datum in self.pp.srcPeriod.datumL:
            
            for comp in self.pp.srcCompL:
                
                if self.pp.process.parameters.asscript:
            
                    today = mj_dt.Today()
                    
                    scriptFP = os.path.join('/Volumes',self.pp.dstPath.volume, self.pp.procsys.dstsystem, self.pp.dstCompD[comp].source,'region','reprojectscript')
                    
                    if not os.path.exists(scriptFP):
                        
                        os.makedirs(scriptFP)
                        
                    scriptFN = 'gdaldem-%(mode)s_%(comp)s-%(today)s.sh' %{'mode':self.pp.process.parameters.mode, 'comp':comp, 'today':today}
                    
                    scriptFPN = os.path.join(scriptFP,scriptFN)
                    
                    self.scriptFPND[comp] = scriptFPN
                
                    self.scriptFD[comp] = open(scriptFPN,'w')
                    
                    writeln = '# Script created by Kartturs GeoImagine Framework for DEM processing %s, created %s\n' %(comp, today)
            
                    self.scriptFD[comp].write(writeln)
                
                for locus in self.pp.srcLayerD:
                                        
                    srcLayer = self.pp.srcLayerD[locus][datum][comp]
                    
                    if self.pp.process.parameters.mosaic:
                        
                        srcLayerFPN = srcLayer.FPN.replace(srcLayer.comp.ext, '-full.vrt')
                        
                        if not os.path.exists(srcLayerFPN):
                            
                            exitstr = 'EXITING, expecting a virtual mosaic as input for GDALDEMTiles\n    %s' %(srcLayerFPN)
                            
                            print (exitstr)
                            
                            SNULLE
                            
                            exit(exitstr)
                              
                    else:
                        
                        srcLayerFPN = srcLayer.FPN
                        
                    srcProjStuff, srcLayerStuff = GetRasterMetaData(srcLayerFPN)
                           
                    dstLayerFP, iniDstLayerFN = os.path.split(self.pp.dstLayerD[locus][datum][comp].FPN)
                    
                    radiusL = self.pp.process.parameters.radiuscsv.split(',')
                    
                    radiusL = [int(r) for r in radiusL] 
                    
                    if hasattr(self.pp.process.parameters,'tr_xres'):
                        
                        tr_xres = self.pp.process.parameters.tr_xres
                        
                        tr_yres = self.pp.process.parameters.tr_xres
                        
                    else:
                        
                        tr_xres = srcLayerStuff.cellsize
                        
                        tr_yres = srcLayerStuff.cellsize
                        
                    for radius in radiusL:
                        
                        # Get the input file and size afresh in each loop
                        
                        if self.pp.process.parameters.mosaic:
                        
                            srcLayerFPN = srcLayer.FPN.replace(srcLayer.comp.ext, '-full.vrt')
                        
                        else:
                            
                            srcLayerFPN = srcLayer.FPN
                                
                        xsize = srcLayerStuff.cols
                        
                        ysize = srcLayerStuff.lins
                        
                        kernel = 3*radius
                        
                        base, ext = os.path.splitext(iniDstLayerFN)
                        
                        resolFN = '%s-%sx%s%s' %(base,kernel,kernel,ext)
                        
                        dstLayerFPN = os.path.join(dstLayerFP,resolFN) 
                        
                        if os.path.exists(dstLayerFPN) and not self.pp.process.overwrite:
                            
                            if self.verbose:
                            
                                infostr = '            Layer already exists: %s' %(dstLayerFPN)
                                
                                print (infostr)
                        
                            continue
                    
                        elif os.path.exists(dstLayerFPN) and self.pp.process.overwrite:
                            
                            if self.verbose:
                            
                                infostr = '            Overwriting existing layer: %s' %(dstLayerFPN)
                                
                                print (infostr)
                                
                            os.remove(dstLayerFPN)
                            
                        elif not os.path.exists(dstLayerFP):
                            
                            os.makedirs(dstLayerFP)
                            
                        if self.pp.process.parameters.mosaic:
                            
                            dstLayerFPN = os.path.join(dstLayerFP,'temp.tif')
                        
                        if self.verbose:
                                
                            infostr = '            %sx%s kernel DEM analysis %s for tile: %s' %(kernel,kernel,self.pp.process.parameters.mode, locus )
                            
                            print (infostr)
                            
                        if radius > 1:
                            
                            if not self.pp.process.parameters.mosaic:
                                
                                exitstr = 'EXITING - analysing rasters with radius > 1 requires virtual mosaic tiles'
                                
                                exit(exitstr) 
                            
                            # fit the input layer to the kernel
                            
                            while True:
                                
                                if xsize % kernel == 0:
                                    
                                    self.pp.process.parameters.width = xsize/radius
                                    
                                    break
                                
                                xsize -= 1
                                
                            while True:
                                
                                if ysize % kernel == 0:
                                    
                                    self.pp.process.parameters.height = ysize/radius
                                    
                                    break
                                
                                ysize -= 1
                                
                            #Adjust the tile edges to fit
                                
                            self.pp.process.parameters.dst_ulx = srcLayerStuff.bounds[0]
                            
                            self.pp.process.parameters.dst_lry = srcLayerStuff.bounds[1]
                                    
                            self.pp.process.parameters.dst_lrx = srcLayerStuff.bounds[0] + (srcLayerStuff.cellsize*xsize)
                                    
                            self.pp.process.parameters.dst_uly = srcLayerStuff.bounds[1] + (srcLayerStuff.cellsize*ysize)
                                
                            # Create the low resolution source file
                            
                            lowresolSrcFPN = os.path.join(dstLayerFP,'lowresol.tif')
                            
                            self.pp.process.parameters.tr_xres = tr_xres*radius
                            
                            self.pp.process.parameters.tr_yres = tr_yres*radius
                            
                            self.pp.process.parameters.resample = 'average'    
                                
                            self._GdalTranslate(lowresolSrcFPN, srcLayerFPN)

                            srcLayerFPN = lowresolSrcFPN
                            
                        self.pp.process.parameters.resample = 'near'
                        
                        if self.pp.process.parameters.mode == 'slope':
                            
                            self._GdalDemSlope(dstLayerFPN, srcLayerFPN)
                            
                        elif self.pp.process.parameters.mode == 'aspect':
                            
                            self._GdalDemAspect(dstLayerFPN, srcLayerFPN)
                            
                        elif self.pp.process.parameters.mode == 'hillshade':
                            
                            self._GdalDemHillshade(dstLayerFPN, srcLayerFPN)
                            
                        elif self.pp.process.parameters.mode == 'color-relief':
                            
                            self._GdalDemColorRelief(dstLayerFPN, srcLayerFPN)
                        
                        elif self.pp.process.parameters.mode == 'TRI':
                            
                            self._GdalDemTRI(dstLayerFPN, srcLayerFPN)
                            
                        elif self.pp.process.parameters.mode == 'TPI':
                            
                            self._GdalDemTPI(dstLayerFPN, srcLayerFPN)
                            
                        elif self.pp.process.parameters.mode == 'roughness':
                            
                            self._GdalDemRoughness(dstLayerFPN, srcLayerFPN)
    
                        else:
                            
                            exitstr = 'EXITING - unrecognized command for GDAL DEM: %s' %(self.pp.process.parameters.mode)
                            
                            exit(exitstr)
                            
                        if self.pp.process.parameters.mosaic:
                                                    
                            if self.pp.procsys.srcsystem == 'modis':
                                
                                queryD = {'hvtile': locus}
                                
                                paramL = ['minsinx','minysin','maxxsin','maxysin']
                                
                            elif self.pp.procsys.srcsystem[0:4] == 'ease':
                                
                                queryD = {'xytile': locus}
                                
                                paramL = ['minxease','minyease','maxxease','maxyease']
                                
                            else:
                                
                                exitstr = 'unknown system %s in _GdalDemTiles' %(self.pp.procsys.srcsystem)
                                
                                exit(exitstr)
                                                                                        
                            infostr = '            Cutting down mosaic to region: %s' %(resolFN )
                            
                            print (infostr)
                                
                            extent = self.session._SingleSearch(queryD, paramL, self.pp.procsys.srcsystem,'tilecoords')
                            
                            self.pp.process.parameters.dst_ulx = extent[0]
                            
                            self.pp.process.parameters.dst_lry = extent[1]
                            
                            self.pp.process.parameters.dst_lrx = extent[2]
                            
                            self.pp.process.parameters.dst_uly = extent[3]
                            
                            self.pp.process.parameters.width = int(round(  (extent[2]-extent[0])/ tr_xres))
                            
                            self.pp.process.parameters.height = int(round(  (extent[3]-extent[1])/ tr_yres))
                            
                            self.pp.process.parameters.tr_xres = tr_xres
                            
                            self.pp.process.parameters.tr_yres = tr_yres
                            
                            self.pp.process.parameters.resample = 'near' 
                            
                            self._GdalWarp(os.path.join(dstLayerFP,resolFN), dstLayerFPN)
                            
                            os.remove(dstLayerFPN)
                            
                            if radius > 1:
                            
                                os.remove(lowresolSrcFPN)
  
    def _GdalDemRegion(self):
        '''
        '''
        
        
        self.scriptFD = {}; self.scriptFPND = {}
        
        if self.pp.process.parameters.asscript:
            
            today = mj_dt.Today()
            
            for comp in self.pp.dstCompD:
                
                scriptFP = os.path.join('/Volumes',self.pp.dstPath.volume, self.pp.procsys.dstsystem, self.pp.dstCompD[comp].source,'region','reprojectscript')
                
                if not os.path.exists(scriptFP):
                    
                    os.makedirs(scriptFP)
                    
                scriptFN = 'gdaldem-%(mode)s_%(comp)s-%(today)s.sh' %{'mode':self.pp.process.parameters.mode, 'comp':comp, 'today':today}
                
                scriptFPN = os.path.join(scriptFP,scriptFN)
                
                self.scriptFPND[comp] = scriptFPN
                
                self.scriptFD[comp] = open(scriptFPN,'w')
                
                writeln = '# Script created by Kartturs GeoImagine Framework for DEM processing %s, created %s\n' %(comp, today)
        
                self.scriptFD[comp].write(writeln)
                      
        for srcLocus in self.pp.srcLayerD:
                        
            for datum in self.pp.srcLayerD[srcLocus]:
                          
                for comp in self.pp.srcLayerD[srcLocus][datum]:
                                        
                    if not os.path.exists(self.pp.srcLayerD[srcLocus][datum][comp].FPN):
                    
                        exitstr = 'EXITING - region layer for tiling missing\n    %s' %(self.pp.srcLayerD[srcLocus][datum][comp].FPN)
            
                        exit(exitstr)
                        
                    # Loop over all destination tiles with the same comp and datum
                    
                    for locus in self.pp.dstLayerD:
                        
                        dstLayer = self.pp.dstLayerD[locus][datum][comp]
                        
                        print ('dstLayer',dstLayer.FPN)
                        
                        if not dstLayer._Exists(): 
                        
                            if self.verbose > 1:
                            
                                infostr = '            DAM analysis %s for region: %s' %(self.pp.process.parameters.mode, dstLayer.FPN )
                                
                            if self.pp.process.parameters.mode == 'slope':
                                
                                self._GdalDemSlope(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                                
                            elif self.pp.process.parameters.mode == 'aspect':
                                
                                self._GdalDemAspect(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                                
                            elif self.pp.process.parameters.mode == 'hillshade':
                                
                                self._GdalDemHillshade(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                                
                            elif self.pp.process.parameters.mode == 'color-relief':
                                
                                self._GdalDemColorRelief(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                            
                            elif self.pp.process.parameters.mode == 'TRI':
                                
                                self._GdalDemTRI(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                                
                            elif self.pp.process.parameters.mode == 'TPI':
                                
                                self._GdalDemTPI(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)
                                
                            elif self.pp.process.parameters.mode == 'roughness':
                                
                                self._GdalDemRoughness(dstLayer.FPN, self.pp.srcLayerD[srcLocus][datum][comp].FPN)

                            else:
                                
                                exitstr = 'EXITING - unrecognized command for GDAL DEM: %s' %(self.pp.process.parameters.mode)
                                
                                exit(exitstr)
