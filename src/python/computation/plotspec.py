#!/usr/local/uvcdat/1.3.1/bin/python

# general-purpose classes (i.e., not specific to any GUI or diagnostic group) used in computing data for plots
from metrics.common import *
from metrics.common.id import *
from metrics.packages.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend import *
import sys, traceback, logging

logger = logging.getLogger(__name__)

class derived_var(basic_id):
    IDtuple = namedtuple( "derived_var_ID", "classid var varmod season ft1 ft2 region" )

    def __init__( self, vid, inputs=[], outputs=['output'], func=(lambda: None), special_values=None,
                  special_orders={} ):
        """Arguments:
        vid, an id for this dervied variable;
        func=function to compute values of this variable;
        inputs=list of ids of the variables which are the inputs to func;
        outputs=list of ids of variables which are outputs of func (default is a single output
           quantity named 'output');
        """
        if type(vid) is tuple or type(vid) is self.IDtuple:
            basic_id.__init__(self,*vid)
        else:  # probably vid is a string
            basic_id.__init__(self,vid)
        #self._vid = self._strid      # self._vid is deprecated
        self._inputs = [i for i in inputs if i is not None]
        self._outputs = outputs
        self._func = func
        self._file_attributes = {}
        # This is primarily used for 2-phase derived variables where we need to pass in a
        # special value that wouldn't be part of the input dictionary. The current example is
        # passing in a region and weights for land set 5 when we compute reduced/derived variables, then
        # construct new variables based on those which all require a 'region' argument.
        # I could see this being used for passing in seasons perhaps as well, and perhaps
        # any other arbitary sort of argument. Perhaps there is a better way of doing this,
        # but this is what worked for me in land.
        #   -BES
        self._special = special_values
        # Only example so far of "special_orders":  { 'T':'dontreduce' }
        # which means that an input T should not be reduced as input variables usually are, before
        # computing a derived variable .
        self.special_orders = special_orders
    def inputs( self ):
        return self._inputs
    def derive( self, inpdict ):
        """Compute the derived variable.  inpdict is a dictionary of input names (ids) and
        values, and will be used to get the input values from the input names in self._inputs.
        Typically an key of inpdict will be the name of a reduced variable, or another derived
        variable; and the corresponding value will be an MV (i.e. cdms2 variable, usually a
        TransientVariable).  But the key could also represent a choice made by the user in the GUI
        or the controlling script, e.g. 'seasonid' or 'region'.  Then the value will typically be a
        string (By convention we say 'seasonid' for a string and 'season' for a cdutil.times.Seasons
        object)."""
        # error from checking this way!... if None in [ vardict[inp] for inp in self._inputs ]:
        if self._special != None:
           # First, we have to add to inpdict to make sure the special_values isn't thrown away.
#           print 'inpdict: ', inpdict
#           print 'inpdict type:' ,type(inpdict)
#           print 'special: ', type(self._special)
           for k in self._special:
            inpdict[k] = k
#           inpdict[self._special] = self._special
#           print 'inpdict after'
#           print type(self._inputs)
           # Then we need to add it to inputs
           self._inputs.extend(self._special)
        dictvals = [ inpdict.get(inp,None) for inp in self._inputs ]
        nonevals = [ inp for inp in self._inputs if inpdict.get(inp,None) is None ]
        for var in dictvals:
            # set some attributes which may help do a mass-weighted mean computation
            if not hasattr(self,'filename') and hasattr(var,'filename'):
                self.filename = var.filename
                if not hasattr(self,'filetable') and hasattr(var,'filetable'):
                    self.filetable = var.filetable
                    break
            elif not hasattr(self,'filetable') and hasattr(var,'filetable'):
                self.filetable = var.filetable
        if len(nonevals)>0:
            logger.warning("cannot yet derive %s because missing inputs %s",self._id,nonevals)
            logger.debug("what's available is %s", inpdict.keys())
            return None
        try:
            output = apply( self._func, [ inpdict[inp] for inp in self._inputs ] )
        except TypeError as e:
            logger.error("In derived_var.derive, _inputs=%s",self._inputs)
            logger.exception("Derivation function failed.  Probably not enough valid inputs.")
            return None
        if type(output) is tuple or type(output) is list or\
                str(type(output)).find('_ID')>0:
            #   If output be a named tuple  used for ID, it will contain the string _ID
            for o in output:
                if o is None: return None
                #o._vid  = self._vid      # self._vid is deprecated
                self.adopt( o )  # o gets ids of self
                if hasattr(self,'filename'):  o.filename = self.filename
                if hasattr(self,'filetable'):  o.filetable = self.filetable
                self._file_attributes.update( getattr(o,'_file_attributes',{}) )
        elif output is not None:
            #output._vid = self._vid      # self._vid is deprecated
            self.adopt( output )  # output gets ids of self
            if hasattr(self,'filename'):  output.filename = self.filename
            if hasattr(self,'filetable'):  output.filetable = self.filetable
            self._file_attributes.update( getattr(output,'_file_attributes',{}) )

            # Compute the mean right away.  Clearing the weight cache and especially this method
            # for doing it just once, are a temporary expedients;
            outaxes = [ax.axis for ax in output.getAxisList() if hasattr(ax,'axis')]
            outaxes.sort()
            if outaxes==['X','Y','Z'] and 'mass' in getattr(output.filetable,'weights',{}):
                # This is the kind of domain we want to save mass weights for.
                # Whatever mass weights are in the filetable might be bad - that happens if it has
                # mass weights for hybrid levels and we're now using pressure levels.
                # So clear it out. New ones will get computed.
                # This operation will be unnecessary once I implement something better than (latsize,lonsize)
                # for looking up mass weights.
                output.filetable.weights['mass']={}
            output.mean = None  # ensures that set_mean will compute a new mean.
            #   Note that the previous calculation may have transmitted the :mean attribute from an
            #   input variable to output, which would be incorrect.
            #not needed: set_mean(output)
        if hasattr(output,'__cdms_internals__'):  # probably a mv
            output.id = underscore_join(output._id)
        return output
    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None, region='' ):
        """varid, varmod, seasonid are strings identifying a variable name, a name modifier
        (often '' is a good value) and season, ft is a filetable, or a string id for the filetable.
        This method constructs and returns an id for the corresponding derived_var object."""
        if seasonid=='JFMAMJJASOND':
            seasonid = 'ANN'
        if type(ft1) is str:  # can happen if id has already been computed, and is used as input here.
            ft1id = ft1
        else:
            ft1id = id2str( ft1._id )
        if ft2 is None or ft2=='':
            ft2id = ''
        elif type(ft2) is str:
            ft2id = ft2
        else:
            ft2id = id2str( ft2._id )
        if region is None:
            regs = ''
        else:
            regs = str(region)
        new_dict_id = basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id, regs )
        return new_dict_id

class dv(derived_var):
    """same as derived_var, but short name saves on typing"""
    pass

class plotspec(basic_id):
    IDtuple = namedtuple( "plotspec_ID", "classid var varmod season ft1 ft2 region" )

    def __init__(
        self, vid,
        zvars=[], zfunc=None, zrangevars=[], zrangefunc=None, zlinetype='solid', zlinecolor=241,
        z2vars=[], z2func=None, z2rangevars=[], z2rangefunc=None, z2linetype='solid', z2linecolor=241,
        z3vars=[], z3func=None, z3rangevars=[], z3rangefunc=None, z3linetype='solid', z3linecolor=241,
        z4vars=[], z4func=None, z4rangevars=[], z4rangefunc=None, z4linetype='solid', z4linecolor=241,
        plottype='table',
        title = None,
        title1 = None,
        title2 = None,
        file_descr = None, # 'descr' field for forming a filename
        source = '',
        overplotline = False,
        levels = None,  # deprecated
        plotparms = None,
        displayunits = None, #units to be used for display,
        more_id=None         # more information to identify the plot
        ):
        """Initialize a plotspec (plot specification).  Inputs are an id and plot type,
        and lists of x,y,z variables (as keys in the plotvars dictionary), functions to
        transform these variables to the quanitity plotted, and a plot type (a string).
        A recommended range in z can be computed by applying zrangefunc to zrangevars;
        the normal use of this feature is to make two plots compatible.  Alternate graph
        axes may be specified - e.g. ya to substitute for y in a plot, or ya1 as an addition
        to y in the plot.
        """
        if plotparms is not None:
            if 'levels' in plotparms: levels = plotparms['levels']
            self.plotparms = plotparms
        if type(vid) is tuple or type(vid) is self.IDtuple:
            # probably this is an id tuple with the first element stripped off
            basic_id.__init__(self,*vid)
        else:
            basic_id.__init__(self,vid)

        if zfunc==None:
            if len(zvars)==0:
                zfunc = (lambda: None)
            else:
                zfunc = (lambda z: z)
        if zrangefunc==None:
            zrangefunc = (lambda: None)

        if z2func==None:
            if len(z2vars)==0:
                z2func = (lambda: None)
            else:
                z2func = (lambda z2: z2)
        if z2rangefunc==None:
            z2rangefunc = (lambda: None)
        
        if z3func==None:
            if len(z3vars) == 0:
               z3func = (lambda: None)
            else:
               z3func = (lambda z3 :z3)
        if z3rangefunc == None:
            z3rangefunc = (lambda: None)

        if z4func==None:
            if len(z4vars) == 0:
               z4func = (lambda: None)
            else:
               z4func = (lambda z4 :z4)
        if z4rangefunc == None:
            z4rangefunc = (lambda: None)

        self.zfunc = zfunc
        self.zvars = zvars
        self.zrangevars = zrangevars
        self.zrangefunc = zrangefunc
        self.zlinetype = zlinetype
        self.zlinecolor = zlinecolor
        
        self.z2func = z2func
        self.z2vars = z2vars
        self.z2rangevars = z2rangevars
        self.z2rangefunc = z2rangefunc
        self.z2linetype = z2linetype
        self.z2linecolor = z2linecolor
        
        self.z3func = z3func
        self.z3vars = z3vars
        self.z3rangevars = z3rangevars
        self.z3rangefunc = z3rangefunc
        self.z3linetype = z3linetype
        self.z3linecolor = z3linecolor
        
        self.z4func = z4func
        self.z4vars = z4vars
        self.z4rangevars = z4rangevars
        self.z4rangefunc = z4rangefunc
        self.z4linetype = z4linetype
        self.z4linecolor = z4linecolor
        
        self.plottype = plottype
        if title is not None:
            self.title = title
        if title1 is not None:
            self.title1 = title1
        if title2 is not None:
            self.title2 = title2
        if file_descr is not None:
            self.file_descr = file_descr
        self.source = source
        self.overplotline = overplotline
        self.levels = levels
        self.displayunits = displayunits
        self.more_id = more_id

    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None, region='' ):
        """This method computes and returns an id for a plotspec object.
        This method is similar to the corresponding method for a derived variable because a plot
        is normally a representation of a variable.
        varid, varmod, seasonid are strings identifying a variable name, a name modifier
        (often '' is a good value) and season, ft is a filetable, or a string id for the filetable."""
        if seasonid=='JFMAMJJASOND':
            seasonid = 'ANN'
        if ft1 is None or ft1=='':
            ft1id = ''
        elif type(ft1) is str:  # can happen if id has already been computed, and is used as input here.
            ft1id = ft1
        else:
            ft1id = id2str( ft1._id )
        if ft2 is None or ft2=='':
            ft2id = ''
        elif type(ft2) is str:
            ft2id = ft2
        else:
            ft2id = id2str( ft2._id )
        if region is None:
            regs = ''
        else:
            regs = str(region)
        new_dict_id = basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id, regs )
        return new_dict_id
    @classmethod
    def dict_idid( cls, otherid ):
        """The purpose of this method is the same as dict_id, except that the input is the id of
        another object, a reduced or derived variable.  It should be a named tuple."""
        # I'd rather name this dict_id, but Python (unlike Common Lisp or C++) doesn't automatically
        # dispatch to one of several function definitions.  Doing it by hand with *args is messier.
        if str(type(otherid)).find('_ID')<0:
            #   If output be a named tuple  used for ID, it will contain the string _ID
            if otherid is None:
                return cls.dict_id( None, None, None, None, None )
            else:
                logger.error("Bad input to plotspec.dict_idid(), not a named tuple. Value is %s, %s",
                             otherid, type(otherid))
                return None

        var    = getattr( otherid, 'var', '' )
        varmod = getattr( otherid, 'varmod', '' )
        season = getattr( otherid, 'season', '' )
        ft1    = getattr( otherid, 'ft1', '' )
        ft2    = getattr( otherid, 'ft2', '' )
        region = getattr( otherid, 'region', '' )

        return cls.dict_id( var, varmod, season, ft1, ft2, region )

    def __repr__(self):
        # return "plotspec _id=%s xvars=%s xfunc=%s yvars=%s yfunc=%s zvars=%s zfunc=%s" %\
        #     (self._strid,self.xvars,self.xfunc.__name__,self.yvars,self.yfunc.__name__,\
        #          self.zvars,self.zfunc.__name__)
        return "plotspec _id=%s zvars=%s zfunc=%s z2vars=%s z2func=%s" %\
            (self._strid, self.zvars,self.zfunc.__name__, self.z2vars,self.z2func.__name__)
    
class ps(plotspec):
    """same as plotspec, but short name saves on typing"""
    pass

class basic_two_line_plot( plotspec ):
    def __init__( self, zvar, z2var, plotparms=None ):
        """zvar, z2var should be the actual vertical values (y-axis) of the plots.
        They should already have been reduced to 1-D variables.
        The horizontal axis is the axis of z*var."""
        # plotspec.__init__( self, y1vars=[y1var], y2vars=[y2var],
        #                    vid = y1var.variableid+y2var.variableid+" line plot", plottype='Yxvsx' )
        plotspec.__init__( self, zvars=[zvar], z2vars=[z2var], plotparms=plotparms,
                           vid = z2var.variableid+z2var.variableid+" line plot", plottype='Yxvsx' )

class one_line_diff_plot( plotspec ):
    def __init__( self, zvar, z2var, vid, plotparms=None ):
        """z*var should be the actual vertical values (y-axis) of the plots.
        z*var should already have been reduced to 1-D variables.
        The horizontal axis of the plot is the axis of z*."""
        plotspec.__init__( self,
            zvars=[zvar,z2var],
            zfunc=aminusb_1ax,   # aminusb_1ax(y1,y2)=y1-y2; each y has 1 axis, use min axis
            vid=vid, plotparms=plotparms,
            plottype='Yxvsx' )

class basic_plot_variable():
    """represents a variable to be plotted.  This need not be an actual data variable;
       it could be some derived quantity"""
    def __init__( self, name, plotset_name, package ):
        self.name = name
        self.plotset_name = plotset_name
        self.package = package
    @staticmethod
    def varoptions(*args,**kwargs):
        """returns a represention of options specific to this variable.  Example dict items:
         'vertical average':'vertavg'
         '300 mbar level value':300
        """
        return None
    
class basic_level_variable(basic_plot_variable):
    """represents a typical variable with a level axis, in a plot set which reduces the level
    axis."""
    pass
    
class level_variable_for_amwg_set5(basic_level_variable):
    """represents a level variable, but has options for AMWG plot set 5"""
    @staticmethod
    def varoptions(*args,**kwargs):
        """returns a represention of options specific to this variable.  Example dict items:
         'vertical average':'vertavg'
         '300 mbar level value':300
        """
        opts = {
            "default":"vertical average", " vertical average":"vertical average",
            "200 mbar":200, "300 mbar":300, "500 mbar":500, "850 mbar":850,
            "200":200, "300":300, "500":500, "850":850,
            }
        return opts

class basic_pole_variable(basic_plot_variable):
    """represents a typical variable that reduces the latitude axis."""
    @staticmethod
    def varoptions():
        """returns the hemisphere specific to this variable. """
        opts ={" Northern Hemisphere":(90, 0.), " Southern Hemisphere":(-90.,0) }
        opts['default'] = (90, 0.)
        return opts
class station_id_variable(basic_plot_variable):
    """provides an index into a data array for a specific station."""
    @staticmethod
    def varoptions():
        """returns the station index specific to this variable. """
        #copied from profiles.ncl in amwg diagnostics

        opts ={}
        data_index = 0
        for station in defines.station_names:
            opts[station] = data_index
            data_index += 1
        opts['default'] = 26  # San Francisco (actually Hayward)
        return opts
