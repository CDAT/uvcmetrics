#!/usr/local/uvcdat/1.3.1/bin/python

# general-purpose classes used in computing data for plots
from metrics.common import *
from metrics.common.id import *

class derived_var(basic_id):
    def __init__( self, vid, inputs=[], outputs=['output'], func=(lambda: None) ):
        if type(vid) is tuple:
            basic_id.__init__(self,*vid)
        else:  # probably vid is a string
            basic_id.__init__(self,vid)
        #self._vid = self._strid      # self._vid is deprecated
        self._inputs = inputs
        self._outputs = outputs
        self._func = func
        self._file_attributes = {}
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
        dictvals = [ inpdict.get(inp,None) for inp in self._inputs ]
        nonevals = [nn for nn in dictvals if nn is None]
        if len(nonevals)>0:
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
        return output
    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None ):
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
        return basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id )

class dv(derived_var):
    """same as derived_var, but short name saves on typing"""
    pass

class plotspec(basic_id):
    def __init__(
        self, vid,
        # xvars=[], xfunc=None, x1vars=[], x1func=None,
        # x2vars=[], x2func=None, x3vars=[], x3func=None,
        # yvars=[], yfunc=None, y1vars=[], y1func=None,
        # y2vars=[], y2func=None, y3vars=[], y3func=None,
        # yavars=[], yafunc=None, ya1vars=[], ya1func=None,
        zvars=[], zfunc=None, zrangevars=[], zrangefunc=None,
        z2vars=[], z2func=None, z2rangevars=[], z2rangefunc=None,
        plottype='table'
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
        # if xfunc==None:
        #     if len(xvars)==0:
        #         xfunc = (lambda: None)
        #     else:
        #         xfunc = (lambda x: x)
        # if x1func==None:
        #     if len(x1vars)==0:
        #         x1func = (lambda: None)
        #     else:
        #         x1func = (lambda x: x)
        # if x2func==None:
        #     if len(x2vars)==0:
        #         x2func = (lambda: None)
        #     else:
        #         x2func = (lambda x: x)
        # if x3func==None:
        #     if len(x3vars)==0:
        #         x3func = (lambda: None)
        #     else:
        #         x3func = (lambda x: x)
        # if yfunc==None:
        #     if len(yvars)==0:
        #         yfunc = (lambda: None)
        #     else:
        #         yfunc = (lambda y: y)
        # if y1func==None:
        #     if len(y1vars)==0:
        #         y1func = (lambda: None)
        #     else:
        #         y1func = (lambda y: y)
        # if y2func==None:
        #     if len(y2vars)==0:
        #         y2func = (lambda: None)
        #     else:
        #         y2func = (lambda y: y)
        # if y3func==None:
        #     if len(y3vars)==0:
        #         y3func = (lambda: None)
        #     else:
        #         y3func = (lambda y: y)
        # if yafunc==None:
        #     if len(yavars)==0:
        #         yafunc = (lambda: None)
        #     else:
        #         yafunc = (lambda ya: ya)
        # if ya1func==None:
        #     if len(ya1vars)==0:
        #         ya1func = (lambda: None)
        #     else:
        #         ya1func = (lambda ya: ya)
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
        # self.xfunc = xfunc
        # self.xvars = xvars
        # self.x1func = x1func
        # self.x1vars = x1vars
        # self.x2func = x2func
        # self.x2vars = x2vars
        # self.x3func = x3func
        # self.x3vars = x3vars
        # self.yfunc = yfunc
        # self.yvars = yvars
        # self.y1func = y1func
        # self.y1vars = y1vars
        # self.y2func = y2func
        # self.y2vars = y2vars
        # self.y3func = y3func
        # self.y3vars = y3vars
        # self.yafunc = yafunc
        # self.yavars = yavars
        # self.ya1func = ya1func
        # self.ya1vars = ya1vars
        self.zfunc = zfunc
        self.zvars = zvars
        self.zrangevars = zrangevars
        self.zrangefunc = zrangefunc
        self.z2func = z2func
        self.z2vars = z2vars
        self.z2rangevars = z2rangevars
        self.z2rangefunc = z2rangefunc
        self.plottype = plottype

    @classmethod
    def dict_id( cls, varid, varmod, seasonid, ft1, ft2=None ):
        """This method computes an dreturns an id for a uvc_simple_plotspec object.
        This method is similar to the corresponding method for a derived variable because a plot
        is normally a representation of a variable.
        varid, varmod, seasonid are strings identifying a variable name, a name modifier
        (often '' is a good value) and season, ft is a filetable, or a string id for the filetable."""
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
        return basic_id._dict_id( cls, varid, varmod, seasonid, ft1id, ft2id )
    @classmethod
    def dict_idid( cls, otherid ):
        """The purpose of this method is the same as dict_id, except that the input is the id tuple
        of another object, a reduced or derived variable."""
        # I'd rather name this dict_id, but Python (unlike Common Lisp or C++) doesn't automatically
        # dispatch to one of several function definitions.  Doing it by hand with *args is messier.
        if type(otherid) is not tuple:
            print "ERROR.  Bad input to plotspec.dict_idid(), not a tuple."
            print otherid
            return None
        if otherid[0]=='rv' and len(otherid)==4:
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
            print otherid
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
