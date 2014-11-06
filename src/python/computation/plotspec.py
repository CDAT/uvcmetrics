#!/usr/local/uvcdat/1.3.1/bin/python

# general-purpose classes (i.e., not specific to any GUI or diagnostic group) used in computing data for plots
from metrics.common import *
from metrics.common.id import *
from metrics.packages.diagnostic_groups import *
from metrics.computation.reductions import *
import sys, traceback

class derived_var(basic_id):
    def __init__( self, vid, inputs=[], outputs=['output'], func=(lambda: None), special_value=None ):
        """Arguments:
        vid, an id for this dervied variable;
        func=function to compute values of this variable;
        inputs=list of ids of the variables which are the inputs to func;
        outputs=list of ids of variables which are outputs of func (default is a single output
           quantity named 'output');
        """
        if type(vid) is tuple:
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
        # passing in a region for land set 5 when we compute reduced/derived variables, then
        # construct new variables based on those which all require a 'region' argument.
        # I could see this being used for passing in seasons perhaps as well, and perhaps
        # any other arbitary sort of argument. Perhaps there is a better way of doing this,
        # but this is what worked for me in land.
        #   -BES
        self._special = special_value
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
           # First, we have to add to inpdict to make sure the special_value isn't thrown away.
           inpdict[self._special] = self._special
           # Then we need to add it to inputs
           self._inputs.append(self._special)
        dictvals = [ inpdict.get(inp,None) for inp in self._inputs ]
        nonevals = [nn for nn in dictvals if nn is None]
        if len(nonevals)>0:
            print "cannot yet derive",self._id,"because missing inputs",nonevals
            return None
        output = apply( self._func, [ inpdict[inp] for inp in self._inputs ] )
        if type(output) is tuple or type(output) is list:
            for o in output:
                if o is None: return None
                #o._vid  = self._vid      # self._vid is deprecated
                self.adopt( o )  # o gets ids of self
                self._file_attributes.update( getattr(o,'_file_attributes',{}) )
        elif output is not None:
            #output._vid = self._vid      # self._vid is deprecated
            self.adopt( output )  # output gets ids of self
            self._file_attributes.update( getattr(output,'_file_attributes',{}) )
        if hasattr(output,'__cdms_internals__'):  # probably a mv
            output.id = '_'.join(output._id)
        return output
    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None, region=None ):
        """varid, varmod, seasonid are strings identifying a variable name, a name modifier
        (often '' is a good value) and season, ft is a filetable, or a string id for the filetable.
        This method constructs and returns an id for the corresponding derived_var object."""
        if type(ft1) is str:  # can happen if id has already been computed, and is used as input here.
            ft1id = ft1
        else:
            ft1id = id2str( ft1._id )
        if ft2 is None or ft2=='':
            ft2id = ''
        else:
            ft2id = id2str( ft2._id )
        if region is None:
            regs = ''
        else:
            regs = str(region)
        return basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id, str(region) )

class dv(derived_var):
    """same as derived_var, but short name saves on typing"""
    pass

class plotspec(basic_id):
    def __init__(
        self, vid,
        zvars=[], zfunc=None, zrangevars=[], zrangefunc=None,
        z2vars=[], z2func=None, z2rangevars=[], z2rangefunc=None,
        z3vars=[], z3func=None, z3rangevars=[], z3rangefunc=None,
        z4vars=[], z4func=None, z4rangevars=[], z4rangefunc=None,
        plottype='table',
        title = None,
        source = '',
        overplotline = False
        ):
        """Initialize a plotspec (plot specification).  Inputs are an id and plot type,
        and lists of x,y,z variables (as keys in the plotvars dictionary), functions to
        transform these variables to the quanitity plotted, and a plot type (a string).
        A recommended range in z can be computed by applying zrangefunc to zrangevars;
        the normal use of this feature is to make two plots compatible.  Alternate graph
        axes may be specified - e.g. ya to substitute for y in a plot, or ya1 as an addition
        to y in the plot.
        """
        if type(vid) is tuple:
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
        self.zfunc = zfunc
        self.zvars = zvars
        self.zrangevars = zrangevars
        self.zrangefunc = zrangefunc
        
        self.z2func = z2func
        self.z2vars = z2vars
        self.z2rangevars = z2rangevars
        self.z2rangefunc = z2rangefunc
        
        self.z3func = z3func
        self.z3vars = z3vars
        self.z3rangevars = z3rangevars
        self.z3rangefunc = z3rangefunc
        
        self.z4func = z4func
        self.z4vars = z4vars
        self.z4rangevars = z4rangevars
        self.z4rangefunc = z4rangefunc
        
        self.plottype = plottype
        if title is not None:
            self.title = title
        self.source = source
        self.overplotline = overplotline

    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None, region='' ):
        """This method computes and returns an id for a plotspec object.
        This method is similar to the corresponding method for a derived variable because a plot
        is normally a representation of a variable.
        varid, varmod, seasonid are strings identifying a variable name, a name modifier
        (often '' is a good value) and season, ft is a filetable, or a string id for the filetable."""
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
        return basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id, region )
    @classmethod
    def dict_idid( cls, otherid ):
        """The purpose of this method is the same as dict_id, except that the input is the id tuple
        of another object, a reduced or derived variable."""
        # I'd rather name this dict_id, but Python (unlike Common Lisp or C++) doesn't automatically
        # dispatch to one of several function definitions.  Doing it by hand with *args is messier.
        if type(otherid) is not tuple:
            if otherid is None:
                return cls.dict_id( None, None, None, None, None )
            else:
                print "ERROR.  Bad input to plotspec.dict_idid(), not a tuple.  Value is"
                print otherid, type(otherid)
                return None
        if otherid[0]=='rv' and len(otherid)==6 and otherid[5] is None or otherid[5]=='None' or otherid[5]=='':
            otherid = otherid[:5]
        if otherid[0]=='rv' and len(otherid)==5 and otherid[4] is None or otherid[4]=='None' or otherid[4]=='':
            otherid = otherid[:4]
        if otherid[0]=='rv' and len(otherid)==5:
            varid = otherid[1]
            varmod = otherid[4]
            seasonid = otherid[2]
            ft1 = otherid[3]
            ft2 = None
        elif otherid[0]=='rv' and len(otherid)==4:
            varid = otherid[1]
            varmod = ''
            seasonid = otherid[2]
            ft1 = otherid[3]
            ft2 = None
        elif otherid[0]=='dv' and (len(otherid)==5 or len(otherid)==6):
            varid = otherid[1]
            varmod = otherid[2]
            seasonid = otherid[3]
            ft1 = otherid[4]
            if len(otherid)<=5:
                ft2 = None
            else:
                ft2 = otherid[5]
        else:
            print "ERROR.  Bad input to plotspec.dict_idid(), wrong class slot or wrong length."
            print otherid, type(otherid)
            return None
        return cls.dict_id( varid, varmod, seasonid, ft1, ft2 )

    def __repr__(self):
        # return "plotspec _id=%s xvars=%s xfunc=%s yvars=%s yfunc=%s zvars=%s zfunc=%s" %\
        #     (self._strid,self.xvars,self.xfunc.__name__,self.yvars,self.yfunc.__name__,\
        #          self.zvars,self.zfunc.__name__)
        return "plotspec _id=%s zvars=%s zfunc=%s z2vars=%s z2func=%s" %\
            (self._strid, self.zvars,self.zfunc.__name__, self.z2vars,self.z2func.__name__)
    
class ps(plotspec):
    """same as plotspec, but short name saves on typing"""
    pass


# class basic_one_line_plot( plotspec ):
#     def __init__( self, yvar, xvar=None ):
#         # xvar, yvar should be the actual x,y of the plot.
#         # xvar, yvar should already have been reduced to 1-D variables.
#         # Normally y=y(x), x is the axis of y.
#         if xvar is None:
#             xvar = yvar.getAxisList()[0]
#         if xvar == "never really come here":
#             ### modified sample from Charles of how we will pass around plot parameters...
#             vcsx = vcs.init()      # but note that this doesn't belong here!
#             yx=vcsx.createyxvsx()
#             # Set the default parameters
#             yx.datawc_y1=-2  # a lower bound, "data 1st world coordinate on Y axis"
#             yx.datawc_y2=4  # an upper bound, "data 2nd world coordinate on Y axis"
#             plotspec.__init__( self, xvars=[xvar], yvars=[yvar],
#                                vid = yvar.id+" line plot", plottype=yx.tojson() )
#             ### ...sample from Charles of how we will pass around plot parameters
#         else:
#             # This is the real code:
#             plotspec.__init__( self, xvars=[xvar], yvars=[yvar],
#                                vid = yvar.id+" line plot", plottype='Yxvsx' )

class basic_two_line_plot( plotspec ):
    def __init__( self, zvar, z2var ):
        """zvar, z2var should be the actual vertical values (y-axis) of the plots.
        They should already have been reduced to 1-D variables.
        The horizontal axis is the axis of z*var."""
        # plotspec.__init__( self, y1vars=[y1var], y2vars=[y2var],
        #                    vid = y1var.variableid+y2var.variableid+" line plot", plottype='Yxvsx' )
        plotspec.__init__( self, zvars=[zvar], z2vars=[z2var],
                           vid = z2var.variableid+z2var.variableid+" line plot", plottype='Yxvsx' )

class one_line_diff_plot( plotspec ):
    def __init__( self, zvar, z2var, vid ):
        """z*var should be the actual vertical values (y-axis) of the plots.
        z*var should already have been reduced to 1-D variables.
        The horizontal axis of the plot is the axis of z*."""
        plotspec.__init__( self,
            zvars=[zvar,z2var],
            zfunc=aminusb_1ax,   # aminusb_1ax(y1,y2)=y1-y2; each y has 1 axis, use min axis
            vid=vid,
            plottype='Yxvsx' )

# class contour_plot( plotspec ):
#     def __init__( self, zvar, xvar=None, yvar=None, ya1var=None,
#                   xfunc=None, yfunc=None, ya1func=None ):
#         """ zvar is the variable to be plotted.  xvar,yvar are the x,y of the plot,
#         normally the axes of zvar.  If you don't specify, a x=lon,y=lat plot will be preferred.
#         xvar, yvar, zvar should already have been reduced; x,y to 1-D and z to 2-D."""
#         if xvar is None:
#             xvar = zvar
#         if yvar is None:
#             yvar = zvar
#         if ya1var is None:
#             ya1var = zvar
#         if xfunc==None: xfunc=lonvar
#         if yfunc==None: yfunc=latvar
#         vid = ''
#         if hasattr(zvar,'vid'): vid = zvar.vid
#         if hasattr(zvar,'id'): vid = zvar.id
#         plotspec.__init__(
#             self, vid+'_contour', xvars=[xvar], xfunc=xfunc,
#             yvars=[yvar], yfunc=yfunc, ya1vars=[ya1var], ya1func=ya1func,
#             zvars=[zvar], plottype='Isofill' )

# class contour_diff_plot( plotspec ):
#     def __init__( self, z1var, z2var, plotid, x1var=None, x2var=None, y1var=None, y2var=None,
#                    ya1var=None,  ya2var=None, xfunc=None, yfunc=None, ya1func=None ):
#         """We will plot the difference of the two z variables, z1var-z2var.
#         See the notes on contour_plot"""
#         if x1var is None:
#             x1var = z1var
#         if y1var is None:
#             y1var = z1var
#         if ya1var is None:
#             ya1var = z1var
#         if x2var is None:
#             x2var = z2var
#         if y2var is None:
#             y2var = z2var
#         if ya2var is None:
#             ya2var = z2var
#         if xfunc==None: xfunc=lonvar_min
#         if yfunc==None: yfunc=latvar_min
#         plotspec.__init__(
#             self, plotid, xvars=[x1var,x2var], xfunc=xfunc,
#             yvars=[y1var,y2var], yfunc=yfunc, ya1vars=[ya1var,ya2var], ya1func=ya1func,
#             zvars=[z1var,z2var], zfunc=aminusb_2ax, plottype='Isofill' )


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
            " default":"vertical average", " vertical average":"vertical average",
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
        return opts
