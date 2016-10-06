import logging, pdb
from numbers import Number
from pprint import pprint
import cdms2
from metrics.packages.diagnostic_groups import *
from metrics.computation.plotspec import plotspec
from metrics.computation.reductions import set_mean, regridded_vars
from metrics.common.utilities import underscore_join, round2
from metrics.frontend.uvcdat import uvc_simple_plotspec

logger = logging.getLogger(__name__)


class plot_plan(object):
    # ...I made this a new-style class so we can call __subclasses__ .
    package=BasicDiagnosticGroup  # Note that this is a class not an object.
    name = "dummy plot_plan class"  # anything which will get instantiated should have a real plot set name.
    number = '0'    # anything which will get instantiated should have the plot set 'number' which appears in its name
    #                 The number is actually a short string, not a number - e.g. '3' or '4b'.
    def __repr__( self ):
        if hasattr( self, 'plotall_id' ):
            return self.__class__.__name__+'('+self.plotall_id+')'
        else:
            return self.__class__.__name__+' object'
    def __init__(self, seasonid='ANN', *args ):
        self._season_displayid = seasonid
        if seasonid=='ANN' or seasonid is None:
            # cdutil.times.getMonthIndex() (called by climatology()) doesn't recognize 'ANN'
            self._seasonid='JFMAMJJASOND'
        else:
            self._seasonid=seasonid
        self.reduced_variables = {}
        self.derived_variables = {}
        self.variable_values = { 'seasonid':self._seasonid }
        self.single_plotspecs = {}
        self.composite_plotspecs = {}
        self.plotspec_values = {}
        self.computation_planned = False
    def plan_computation( self, seasonid):
        pass
    def _build_label( self, vars, p ):
        yls = []
        for y in vars:
            if type(y) is tuple:
                yl = getattr(y[0],'_strid',None)
                if yl is None:
                    yl = getattr(y[0],'_vid',None)  # deprecated attribute
            else:
                yl = getattr(y,'_strid',None)
                if yl is None:
                    yl = getattr(y,'_vid',None)  # deprecated attribute
            if yl is not None:
                yls.append( yl )
        new_id = underscore_join(yls)
        if new_id is None or new_id.strip()=="": new_id = p+'_2'
        return new_id
    def compute(self,newgrid=0):
        return self.results(newgrid)

    def uniquefts(self, ftlist):
        names = []
        for i in range(len(ftlist)):
            names.append(ftlist[i]._name)
        names = list(set(names))
        return names

    def getfts(self, model, obs):
        if len(model) == 2:
#           print 'Two models'
           filetable1 = model[0]
           filetable2 = model[1]
        if len(model) == 1 and len(obs) == 1:
#           print 'Model and Obs'
            filetable1 = model[0]
            filetable2 = obs[0]
        if len(obs) == 2: # seems unlikely but whatever
#           print 'Two obs'
           filetable1 = obs[0]
           filetable2 = obs[1]
        if len(model) == 1 and (obs != None and len(obs) == 0):
#           print 'Model only'
           filetable1 = model[0]
           filetable2 = None
        if len(obs) == 1 and (model != None and len(model) == 0): #also unlikely
#           print 'Obs only'
           filetable1 = obs[0]
           filetable2 = None
        return filetable1, filetable2

    # This takes the list of filetables and returns 3 lists:
    # 1) the indexes for the duplicatly named fts (the ones that are raw+climos)
    # 2) the indexes for the purely climo fts
    # 3) the indexes for the purely raw fts
    def parse_fts(self, fts):
    # First, find duplicates.
    # eg, if ft[0] = foo, ft[1] = bar, ft[2] = foo, ft[3] = blah, ft[4] = bar it would return
    # [ [0, 2], [1, 4]]
        raw = []
        climo = []
        names = []
        dups = []
        for i in range(len(fts)):
           if fts[i]._climos == 'yes':
               climo.append(i)
           else:
               raw.append(i)
           names.append(fts[i]._name)
        newnames = list(set(names))
        if len(newnames) != len(names):
           dup_list = []
           for i in range(len(fts)):
              dup_list.append([])
              for j in range(len(fts)):
                 if i == j:
                    pass
                 if fts[i]._name == fts[j]._name:
                    dup_list[i].append(j)
           for elem in dup_list:
              if elem not in dups and len(elem) == 2:
                 dups.append(elem)
        return dups, climo, raw 


    def results(self,newgrid=0):
        return self._results(newgrid)
# To profile, replace (by name changes) the above results() with the following one:
    def profiled_results(self,newgrid=0):
        if newgrid!=0:
            logger.error("Haven't implemented profiling with argument")
        prof = cProfile.Profile()
        returnme = prof.runcall( self._results )
        prof.dump_stats('results_stats')
        return returnme
    def _results(self, newgrid=0 ):
        """newgrid=0 for keep original. !=0 to use any regridded variants of variables - presently
        that means a coarser grid, typically from regridding model data to the obs grid.
        In the future regrid>0 will mean regrid everything to the finest grid and regrid<0
        will mean regrid everything to the coarsest grid."""
        for v in self.reduced_variables.keys():
            #print v
            value = self.reduced_variables[v].reduce(None)
            try:
                if  len(value.data)<=0:
                    logger.error("No data for %s",v)
            except: # value.data may not exist, or may not accept len()
                try:
                    if value.size<=0:
                        logger.error("No data for %s",v)
                except: # value.size may not exist
                    pass
            self.variable_values[v] = value  # could be None
            #print value.id, value.shape
            #pdb.set_trace()
        postponed = []   # derived variables we won't do right away

        #print 'derived var'
        for v in self.derived_variables.keys():
            #pdb.set_trace()
            #print v
            value = self.derived_variables[v].derive(self.variable_values)
            #print value.id, value.shape
            if value is None:
                # couldn't compute v - probably it depends on another derived variables which
                # hasn't been computed yet
                postponed.append(v)
            else:
                self.variable_values[v] = value

        #print 'postponed', postponed
        for v in postponed:   # Finish up with derived variables
            #print v
            value = self.derived_variables[v].derive(self.variable_values)
            #print value.id, value.shape
            self.variable_values[v] = value  # could be None
        varvals = self.variable_values

        for p, ps in self.single_plotspecs.iteritems():
            logger.info("Plotplan preparing data for %s and %s", ps._strid, ps.plottype)
            #pdb.set_trace()
            try:
                zax,zrv  = self.compute_plot_var_value( ps, ps.zvars, ps.zfunc )
                z2ax,z2rv = self.compute_plot_var_value( ps, ps.z2vars, ps.z2func )
                z3ax,z3rv = self.compute_plot_var_value( ps, ps.z3vars, ps.z3func )
                z4ax,z4rv = self.compute_plot_var_value( ps, ps.z4vars, ps.z4func )

                if zax is None and z2ax is None and z3ax is None and z4ax is None:
                    continue
            except Exception as e:
                if ps._id != plotspec.dict_id( None, None, None, None, None ):
                    # not an empty plot
                    logger.warning("Cannot compute data for %s due to exception %s %s",ps._strid, e.__class__.__name__, e)
                    import traceback
                    tb = traceback.format_exc()
                    logger.debug("traceback:\n%s", tb)
                self.plotspec_values[p] = None
                continue
            vars = []
            zlab=""
            z2lab=""
            z3lab =""
            z3lab = ""
            if zax is not None:
                zaxdata = getattr(zax,'data',[None])
                try:
                    lenzaxdata = len(zaxdata)  # >0 for a tuple
                except TypeError:
                    lenzaxdata = 0
                if lenzaxdata<=0:
                    logger.warning("No plottable data for %s",getattr(zax,'id',zax))
                    continue
                if hasattr(zax,'regridded') and newgrid!=0:
                    vars.append( regridded_vars[zax.regridded] )
                else:
                    vars.append( zax )
                new_id = self._build_label( zrv, p )
                if type(zax) is not tuple:
                    zax.id = new_id
                    zlab += ' '+zax.id
            if z2ax is not None:
                if hasattr(z2ax,'regridded') and newgrid!=0:
                    vars.append( regridded_vars[z2ax.regridded] )
                else:
                    vars.append( z2ax )
                new_id = self._build_label( z2rv, p )
                z2ax.id = new_id
                z2lab += ' '+z2ax.id
            if z3ax is not None:
               if hasattr(z3ax,'regridded') and newgrid != 0:
                  vars.append( regridded_vars[z3ax.regridded] )
               else:
                  vars.append( z3ax)
               new_id = self._build_label( z3rv, p )
               z3ax.id = new_id
               z3lab += ' '+z3ax.id
            if z4ax is not None:
               if hasattr(z4ax,'regridded') and newgrid != 0:
                  vars.append( regridded_vars[z4ax.regridded] )
               else:
                  vars.append( z4ax)
               new_id = self._build_label( z4rv, p )
               z4ax.id = new_id
               z4lab += ' '+z4ax.id

            if vars==[]:
                self.plotspec_values[p] = None
                continue
            #labels = [xlab,ylab,zlab]
            labels = [zlab,z2lab]
            if hasattr(ps,'title1'):
                title1 = ps.title1
                title = title1      # deprecated
                title2 = getattr( ps, 'title2', title1 )
            elif hasattr(ps,'title'):  # deprecated
                title1 = ps.title
                title = title1
                title2 = getattr( ps, 'title2', title )
            else:  # Normally we won't get here because titles are normally built with the plotspec object.
                title = ' '.join(labels)+' '+self._season_displayid  # do this better later
                title1 = title
                title2 = title
                
            #process the ranges if present
            zrange = ps.zrangevars
            z2range = ps.z2rangevars
            z3range = ps.z3rangevars
            z4range = ps.z4rangevars
            ranges = {}
            if zrange != None and z2range != None and z3range != None and z4range != None:
                ranges.update(ps.zrangevars)
                if ps.z2rangevars:
                   ranges.update(ps.z2rangevars)
                if ps.z3rangevars:
                   ranges.update(ps.z3rangevars)
                if ps.z4rangevars:
                   ranges.upadte(ps.z4rangevars)
            else:
                ranges = None

            #over plot line flag
            overplotline = False
            if  hasattr(ps, 'overplotline'):
                overplotline = ps.overplotline
            
            #get line types for each curve (solid, dot, ...)
            linetypes = [ps.zlinetype]
            if z2ax is not None:
                linetypes += [ps.z2linetype]

            #get the line color for each curve
            linecolors = [ps.zlinecolor]
            if z2ax is not None:
                line2colors = [ps.z2linecolor]

            #get the levels and plot parameters
            levels = ps.levels  # deprecated
            more_id = ps.more_id
            plotparms = getattr(ps,'plotparms',None)
                    
            regionid = getattr(self,'region','')
            if type(regionid) is not str: regionid = regionid.id()[1]
            if regionid.lower().find('global')>=0: regionid=''

            # The following line is getting specific to UV-CDAT, although not any GUI...
            #pdb.set_trace()
            #new kludge added to handle scatter plots, 10/14/14, JMcE
            if self.plottype == 'Vector':
                if type(vars[0])==tuple:
                    plot_type_temp = 'Vector'
                elif vars[0].id.find('STRESS_MAG')>=0:   # maybe not needed
                    # If this is needed, we need to change code so that this isn't.
                    plot_type_temp = 'Isofill'
                else:
                    #jfp not tested yet on wind stress, wrong for moisture transport:
                    #jfp plot_type_temp = self.plottype
                    plot_type_temp = 'Isofill' #jfp works for moisture transport
            else:
                plot_type_temp = ps.plottype
            self.plotspec_values[p] = uvc_simple_plotspec(
                vars, plot_type_temp, labels, title, title1, title2, ps.source, ranges, overplotline, linetypes,
                linecolors, levels=levels, more_id=more_id, plotparms=plotparms, idinfo={
                    'vars':[getattr(self,'varid','')],'season':self._seasonid, 'region':regionid,
                    'ft1':getattr(self,'ft1nom',''), 'ft2':getattr(self,'ft2nom',''),
                    'ft1nn':getattr(self,'ft1nickname',''), 'ft2nn':getattr(self,'ft2nickname','') } )
        #pdb.set_trace()

        # dispose of any failed plots
        self.plotspec_values = { p:ps for p,ps in self.plotspec_values.items() if ps is not None }

        logger.debug('now composite plot')
        for p,ps in self.composite_plotspecs.iteritems():
            self.plotspec_values[p] = [ self.plotspec_values[sp] for sp in ps if sp in self.plotspec_values ]
            self.plotspec_values[p] = [ self.plotspec_values[sp] for sp in ps if sp in self.plotspec_values ]
            # Normally ps is a list of names of a plots, we'll remember its value as a list of their values.
            if type( ps ) is tuple:
                # ps is a tuple of names of simple plots which should be overlapped
                self.plotspec_values[p] = tuple( self.plotspec_values[p] )
            #print p
            #print self.plotspec_values[p]
        #This next loop is a duplicate of the previous loop.  It can be viewed as a cleanup. The reason it's 
        #needed is that there is no guaranteed order of execution with a dictionary.  So if a composite plot
        #is a composite of others then there may be an incomplete plot if the individual plots are defined
        #later.  Plot set 11 is an example of this.  It can happen with plot set 6 too.
        for p,ps in self.composite_plotspecs.iteritems():
            # Normally ps is a list of names of a plots, we'll remember its value as a list of their values.
            self.plotspec_values[p] = [ self.plotspec_values[sp] for sp in ps if sp in self.plotspec_values ]
            if type( ps ) is tuple:
                # ps is a tuple of names of simple plots which should be overlapped
                self.plotspec_values[p] = tuple( self.plotspec_values[p] )
            #print p
            #print self.plotspec_values[p]
        # note: we may have to += other lists into the same ...[p]
        # note: if we have a composite of composites we can deal with it by building a second time
        #print 'leaving _results'
        #print self.plotspec_values.keys()
        return self

    def compute_plot_var_value( self, ps, zvars, zfunc ):
        """Inputs: a plotspec object, a list zvars of precursor variables, and a function zfunc.
        This method computes the variable z to be plotted as zfunc(zvars), and returns it.
        It also returns zrv for use in building a label."""
        vvals = self.variable_values
        zrv = [ vvals[k] for k in zvars ]

        if any([a is None for a in zrv]):
            logger.warning("Cannot compute plot results from zvars=%s\nbecause missing results for %s", ps.zvars, [k for k in ps.zvars if vvals[k] is None])
            return None, None
        z = apply(zfunc, zrv)
        if hasattr(z, 'mask') and z.mask.all():
            logger.debug("in plotplan.py")
            logger.error("All values of %s are missing!", z.id)
            return None, None
        if hasattr(z,'mean') and z.mean!=getattr(z,'_mean',None):
            # If we computed the mean through set_mean() or mean_of_diff(), then there's an equal _mean attribute.
            # If not, we can't trust the mean attribute.  Any calculation, e.g. a=b+c, may have transmitted :mean
            # e.g. a.mean=b.mean.  But _mean doesn't get transmitted that way.
            del z.mean
        if z is not None and not (hasattr(z, 'mean') and isinstance(z.mean, Number)):
            # Compute variable's mean.  For mass weighting, it should have already happened in a
            # dimensionality reduction functions.
            if type(z) is tuple:
                zid = [zz.id for zz in z]
            else:
                zid = z.id
            logger.debug("No 'mean' attribute in variable %s; we may compute it in compute_plot_var_value.", zid)

            set_mean( z, season=getattr(self,'season',None), region=getattr(self,'region',None) )
            if hasattr(z,'mean') and isinstance(z.mean,cdms2.tvariable.TransientVariable) and\
                    z.mean.shape==():
                # ... adding 0.0 converts a numpy array of shape () to an actual number
                z.mean = z.mean.getValue()+0.0
        if (hasattr(z,'mean') and isinstance(z.mean,Number)):
            # VCS display of z.mean has too many digits unless we round:
            z.mean = round2( z.mean, 6 )

        return z, zrv
        
