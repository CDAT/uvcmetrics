
class TemplateOptions(object):
    """
    Template Opetions Object
    It is used to determine what options from a default template
    should be enabled during plot rendering.
    """
    
    __slots__ = ['_box1',
                 '_box2',
                 '_box3',
                 '_box4',
                 '_comment1',
                 '_comment2',
                 '_comment3',
                 '_comment4',
                 '_crdate',
                 '_crtime',
                 '_data',
                 '_dataname',
                 '_file',
                 '_function',
                 '_legend',
                 '_line1',
                 '_line2',
                 '_line3',
                 '_line4',
                 '_logicalmask',
                 '_mean',
                 '_min',
                 '_max',
                 '_source',
                 '_title',
                 '_tname',
                 '_transformation',
                 '_tunits',
                 '_tvalue',
                 '_units',
                 '_xlabel1',
                 '_xlabel2',
                 '_xmintic1',
                 '_xmintic2',
                 '_xname',
                 '_xtic1',
                 '_xtic2',
                 '_xunits',
                 '_xvalue',
                 '_ylabel1',
                 '_ylabel2',
                 '_ymintic1',
                 '_ymintic2',
                 '_yname',
                 '_ytic1',
                 '_ytic2',
                 '_yunits',
                 '_yvalue',
                 '_zname',
                 '_zunits',
                 '_zvalue',
                 'box1',
                 'box2',
                 'box3',
                 'box4',
                 'bomment1',
                 'bomment2',
                 'bomment3',
                 'bomment4',
                 'crdate',
                 'crtime',
                 'data',
                 'dataname',
                 'file',
                 'function',
                 'legend',
                 'line1',
                 'line2',
                 'line3',
                 'line4',
                 'logicalmask',
                 'mean',
                 'min',
                 'max',
                 'source',
                 'title',
                 'tname',
                 'transformation',
                 'tunits',
                 'tvalue',
                 'units',
                 'xlabel1',
                 'xlabel2',
                 'xmintic1',
                 'xmintic2',
                 'xname',
                 'xtic1',
                 'xtic2',
                 'xunits',
                 'xvalue',
                 'ylabel1',
                 'ylabel2',
                 'ymintic1',
                 'ymintic2'
                 'yname',
                 'ytic1',
                 'ytic2',
                 'yunits',
                 'yvalue',
                 'zname',
                 'zunits',
                 'zvalue',
                 'typeName']
    
    def _getbox1(self):
        return self._box1
    def _setbox1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'box1 must be a boolean'
        self._box1=value
    box1=property(_getbox1,_setbox1,None,"Enable box1 option.")

    def _getbox2(self):
        return self._box2
    def _setbox2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'box2 must be a boolean'
        self._box2=value
    box2=property(_getbox2,_setbox2,None,"Enable box2 option.")

    def _getbox3(self):
        return self._box3
    def _setbox3(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'box3 must be a boolean'
        self._box3=value
    box3=property(_getbox3,_setbox3,None,"Enable box3 option.")

    def _getbox4(self):
        return self._box4
    def _setbox4(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'box4 must be a boolean'
        self._box4=value
    box4=property(_getbox4,_setbox4,None,"Enable box4 option.")

    def _getcomment1(self):
        return self._comment1
    def _setcomment1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'comment1 must be a boolean'
        self._comment1=value
    comment1=property(_getcomment1,_setcomment1,None,"Enable comment1 option.")

    def _getcomment2(self):
        return self._comment2
    def _setcomment2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'comment2 must be a boolean'
        self._comment2=value
    comment2=property(_getcomment2,_setcomment2,None,"Enable comment2 option.")

    def _getcomment3(self):
        return self._comment3
    def _setcomment3(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'comment3 must be a boolean'
        self._comment3=value
    comment3=property(_getcomment3,_setcomment3,None,"Enable comment3 option.")

    def _getcomment4(self):
        return self._comment4
    def _setcomment4(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'comment4 must be a boolean'
        self._comment4=value
    comment4=property(_getcomment4,_setcomment4,None,"Enable comment4 option.")

    def _getcrdate(self):
        return self._crdate
    def _setcrdate(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'crdate must be a boolean'
        self._crdate=value
    crdate=property(_getcrdate,_setcrdate,None,"Enable crdate option.")

    def _getcrtime(self):
        return self._crtime
    def _setcrtime(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'crtime must be a boolean'
        self._crtime=value
    crtime=property(_getcrtime,_setcrtime,None,"Enable crtime option.")

    def _getdata(self):
        return self._data
    def _setdata(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'data must be a boolean'
        self._data=value
    data=property(_getdata,_setdata,None,"Enable data option.")

    def _getdataname(self):
        return self._dataname
    def _setdataname(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'dataname must be a boolean'
        self._dataname=value
    dataname=property(_getdataname,_setdataname,None,"Enable dataname option.")

    def _getfile(self):
        return self._file
    def _setfile(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'file must be a boolean'
        self._file=value
    file=property(_getfile,_setfile,None,"Enable file option.")

    def _getfunction(self):
        return self._function
    def _setfunction(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'function must be a boolean'
        self._function=value
    function=property(_getfunction,_setfunction,None,"Enable function option.")

    def _getlegend(self):
        return self._legend
    def _setlegend(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'legend must be a boolean'
        self._legend=value
    legend=property(_getlegend,_setlegend,None,"Enable legend option.")

    def _getline1(self):
        return self._line1
    def _setline1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'line1 must be a boolean'
        self._line1=value
    line1=property(_getline1,_setline1,None,"Enable line1 option.")

    def _getline2(self):
        return self._line2
    def _setline2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'line2 must be a boolean'
        self._line2=value
    line2=property(_getline2,_setline2,None,"Enable line2 option.")

    def _getline3(self):
        return self._line3
    def _setline3(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'line3 must be a boolean'
        self._line3=value
    line3=property(_getline3,_setline3,None,"Enable line3 option.")

    def _getline4(self):
        return self._line4
    def _setline4(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'line4 must be a boolean'
        self._line4=value
    line4=property(_getline4,_setline4,None,"Enable line4 option.")

    def _getlogicalmask(self):
        return self._logicalmask
    def _setlogicalmask(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'logicalmask must be a boolean'
        self._logicalmask=value
    logicalmask=property(_getlogicalmask,_setlogicalmask,None,"Enable logicalmask option.")

    def _getmean(self):
        return self._mean
    def _setmean(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'mean must be a boolean'
        self._mean=value
    mean=property(_getmean,_setmean,None,"Enable mean option.")

    def _getmin(self):
        return self._min
    def _setmin(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'min must be a boolean'
        self._min=value
    min=property(_getmin,_setmin,None,"Enable min option.")

    def _getmax(self):
        return self._max
    def _setmax(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'max must be a boolean'
        self._max=value
    max=property(_getmax,_setmax,None,"Enable max option.")

    def _getsource(self):
        return self._source
    def _setsource(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'source must be a boolean'
        self._source=value
    source=property(_getsource,_setsource,None,"Enable source option.")

    def _gettitle(self):
        return self._title
    def _settitle(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'title must be a boolean'
        self._title=value
    title=property(_gettitle,_settitle,None,"Enable title option.")

    def _gettname(self):
        return self._tname
    def _settname(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'tname must be a boolean'
        self._tname=value
    tname=property(_gettname,_settname,None,"Enable tname option.")

    def _gettransformation(self):
        return self._transformation
    def _settransformation(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'transformation must be a boolean'
        self._transformation=value
    transformation=property(_gettransformation,_settransformation,None,"Enable transformation option.")

    def _gettunits(self):
        return self._tunits
    def _settunits(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'tunits must be a boolean'
        self._tunits=value
    tunits=property(_gettunits,_settunits,None,"Enable tunits option.")

    def _gettvalue(self):
        return self._tvalue
    def _settvalue(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'tvalue must be a boolean'
        self._tvalue=value
    tvalue=property(_gettvalue,_settvalue,None,"Enable tvalue option.")

    def _getunits(self):
        return self._units
    def _setunits(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'units must be a boolean'
        self._units=value
    units=property(_getunits,_setunits,None,"Enable units option.")

    def _getxlabel1(self):
        return self._xlabel1
    def _setxlabel1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xlabel1 must be a boolean'
        self._xlabel1=value
    xlabel1=property(_getxlabel1,_setxlabel1,None,"Enable xlabel1 option.")

    def _getxlabel2(self):
        return self._xlabel2
    def _setxlabel2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xlabel2 must be a boolean'
        self._xlabel2=value
    xlabel2=property(_getxlabel2,_setxlabel2,None,"Enable xlabel2 option.")

    def _getxmintic1(self):
        return self._xmintic1
    def _setxmintic1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xmintic1 must be a boolean'
        self._xmintic1=value
    xmintic1=property(_getxmintic1,_setxmintic1,None,"Enable xmintic1 option.")

    def _getxmintic2(self):
        return self._xmintic2
    def _setxmintic2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xmintic2 must be a boolean'
        self._xmintic2=value
    xmintic2=property(_getxmintic2,_setxmintic2,None,"Enable xmintic2 option.")

    def _getxname(self):
        return self._xname
    def _setxname(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xname must be a boolean'
        self._xname=value
    xname=property(_getxname,_setxname,None,"Enable xname option.")

    def _getxtic1(self):
        return self._xtic1
    def _setxtic1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xtic1 must be a boolean'
        self._xtic1=value
    xtic1=property(_getxtic1,_setxtic1,None,"Enable xtic1 option.")

    def _getxtic2(self):
        return self._xtic2
    def _setxtic2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xtic2 must be a boolean'
        self._xtic2=value
    xtic2=property(_getxtic2,_setxtic2,None,"Enable xtic2 option.")

    def _getxunits(self):
        return self._xunits
    def _setxunits(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xunits must be a boolean'
        self._xunits=value
    xunits=property(_getxunits,_setxunits,None,"Enable xunits option.")

    def _getxvalue(self):
        return self._xvalue
    def _setxvalue(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'xvalue must be a boolean'
        self._xvalue=value
    xvalue=property(_getxvalue,_setxvalue,None,"Enable xvalue option.")

    def _getylabel1(self):
        return self._ylabel1
    def _setylabel1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ylabel1 must be a boolean'
        self._ylabel1=value
    ylabel1=property(_getylabel1,_setylabel1,None,"Enable ylabel1 option.")

    def _getylabel2(self):
        return self._ylabel2
    def _setylabel2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ylabel2 must be a boolean'
        self._ylabel2=value
    ylabel2=property(_getylabel2,_setylabel2,None,"Enable ylabel2 option.")

    def _getymintic1(self):
        return self._ymintic1
    def _setymintic1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ymintic1 must be a boolean'
        self._ymintic1=value
    ymintic1=property(_getymintic1,_setymintic1,None,"Enable ymintic1 option.")

    def _getymintic2(self):
        return self._ymintic2
    def _setymintic2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ymintic2 must be a boolean'
        self._ymintic2=value
    ymintic2=property(_getymintic2,_setymintic2,None,"Enable ymintic2 option.")

    def _getyname(self):
        return self._yname
    def _setyname(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'yname must be a boolean'
        self._yname=value
    yname=property(_getyname,_setyname,None,"Enable yname option.")

    def _getytic1(self):
        return self._ytic1
    def _setytic1(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ytic1 must be a boolean'
        self._ytic1=value
    ytic1=property(_getytic1,_setytic1,None,"Enable ytic1 option.")

    def _getytic2(self):
        return self._ytic2
    def _setytic2(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'ytic2 must be a boolean'
        self._ytic2=value
    ytic2=property(_getytic2,_setytic2,None,"Enable ytic2 option.")

    def _getyunits(self):
        return self._yunits
    def _setyunits(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'yunits must be a boolean'
        self._yunits=value
    yunits=property(_getyunits,_setyunits,None,"Enable yunits option.")

    def _getyvalue(self):
        return self._yvalue
    def _setyvalue(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'yvalue must be a boolean'
        self._yvalue=value
    yvalue=property(_getyvalue,_setyvalue,None,"Enable yvalue option.")

    def _getzname(self):
        return self._zname
    def _setzname(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'zname must be a boolean'
        self._zname=value
    zname=property(_getzname,_setzname,None,"Enable zname option.")

    def _getzunits(self):
        return self._zunits
    def _setzunits(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'zunits must be a boolean'
        self._zunits=value
    zunits=property(_getzunits,_setzunits,None,"Enable zunits option.")

    def _getzvalue(self):
        return self._zvalue
    def _setzvalue(self,value):
        if not isinstance(value,bool):
            raise ValueError, 'zvalue must be a boolean'
        self._zvalue=value
    zvalue=property(_getzvalue,_setzvalue,None,"Enable zvalue option.")

                 
    def __init__(self):
        self._box1           = True
        self._box2           = True
        self._box3           = True
        self._box4           = True
        self._comment1       = True
        self._comment2       = True
        self._comment3       = True
        self._comment4       = True
        self._crdate         = True            
        self._crtime         = True
        self._data           = True
        self._dataname       = True
        self._file           = True
        self._function       = True
        self._legend         = True
        self._line1          = True
        self._line2          = True
        self._line3          = True
        self._line4          = True
        self._logicalmask    = True
        self._mean           = True
        self._min            = True
        self._max            = True
        self._source         = True
        self._title          = True
        self._tname          = True
        self._transformation = True   
        self._tunits         = True
        self._tvalue         = True
        self._units          = True
        self._xlabel1        = True
        self._xlabel2        = True
        self._xmintic1       = True
        self._xmintic2       = True
        self._xname          = True
        self._xtic1          = True
        self._xtic2          = True
        self._xunits         = True
        self._xvalue         = True
        self._ylabel1        = True
        self._ylabel2        = True
        self._ymintic1       = True
        self._ymintic2       = True
        self._yname          = True
        self._ytic1          = True
        self._ytic2          = True
        self._yunits         = True
        self._yvalue         = True
        self._zname          = True
        self._zunits         = True
        self._zvalue         = True

        self.typeName = "TemplateOptions"

    def __iter__(self):
        for attr, value in self.__dict__.iteritems():
            yield attr, value

    def setAllFalse(self):
        self._box1           = False
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = False
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = False
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False
        self._title          = False
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = False
        self._xlabel1        = False
        self._xlabel2        = False
        self._xmintic1       = False
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = False
        self._xtic2          = False
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = False
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = False
        self._ytic1          = False
        self._ytic2          = False
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False


class TemplateOptionsUVWGMulti(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: isofill, vector, boxfill and isoline.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = True
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = True
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = True
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = True
        self._min            = True
        self._max            = True
        self._source         = False
        self._title          = True
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = True
        self._xlabel1        = False
        self._xlabel2        = False
        self._xmintic1       = False
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = False
        self._xtic2          = False
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = False
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = False
        self._ytic1          = False
        self._ytic2          = False
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWGMulti"

class TemplateOptionsUVWGDUDMulti(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: isofill, vector, boxfill and isoline.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = False
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = False
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False
        self._title          = False
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = False
        self._xlabel1        = False
        self._xlabel2        = False
        self._xmintic1       = False
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = False
        self._xtic2          = False
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = False
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = False
        self._ytic1          = False
        self._ytic2          = False
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWGDUDMulti"

class TemplateOptionsUVWGMultiScatter(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: scatter.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = True
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = False
        self._line1          = False
        self._line2          = False
        self._line3          = True
        self._line4          = True
        self._logicalmask    = True
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False  # Still need to decide this one
        self._title          = True
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = True
        self._units          = True
        self._xlabel1        = True
        self._xlabel2        = False
        self._xmintic1       = True
        self._xmintic2       = False
        self._xname          = True
        self._xtic1          = True
        self._xtic2          = False
        self._xunits         = True
        self._xvalue         = True
        self._ylabel1        = True
        self._ylabel2        = False
        self._ymintic1       = True
        self._ymintic2       = False
        self._yname          = True
        self._ytic1          = True
        self._ytic2          = False
        self._yunits         = True
        self._yvalue         = True
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWGMultiScatter"

# class TemplateOptionsUVWGMultiScatter(TemplateOptions):
#     """
#     Template Options Object for multiple plots on a page.
#     This object is used for plots of type: scatter.
#     """
#     def __init__(self):
#         TemplateOptions.__init__(self)
#         self._box1           = True
#         self._box2           = False
#         self._box3           = False
#         self._box4           = False
#         self._comment1       = True
#         self._comment2       = True
#         self._comment3       = True
#         self._comment4       = True
#         self._crdate         = False            
#         self._crtime         = False
#         self._data           = True
#         self._dataname       = False
#         self._file           = False
#         self._function       = False
#         self._legend         = False
#         self._line1          = False
#         self._line2          = False
#         self._line3          = False
#         self._line4          = False
#         self._logicalmask    = False
#         self._mean           = False
#         self._min            = False
#         self._max            = False
#         self._source         = False
#         self._title          = False
#         self._tname          = False
#         self._transformation = False   
#         self._tunits         = False
#         self._tvalue         = False
#         self._units          = False
#         self._xlabel1        = True
#         self._xlabel2        = False
#         self._xmintic1       = False
#         self._xmintic2       = False
#         self._xname          = True
#         self._xtic1          = True
#         self._xtic2          = False
#         self._xunits         = False
#         self._xvalue         = False
#         self._ylabel1        = True
#         self._ylabel2        = False
#         self._ymintic1       = False
#         self._ymintic2       = False
#         self._yname          = True
#         self._ytic1          = True
#         self._ytic2          = False
#         self._yunits         = False
#         self._yvalue         = False
#         self._zname          = False
#         self._zunits         = False
#         self._zvalue         = False

#         self.typeName = "TemplateOptionsUVWGMultiScatter"

class TemplateOptionsUVWGDUDMultiScatter(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: scatter.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = False
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = False
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False
        self._title          = False
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = False
        self._xlabel1        = False
        self._xlabel2        = False
        self._xmintic1       = False
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = False
        self._xtic2          = False
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = False
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = False
        self._ytic1          = False
        self._ytic2          = False
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWGDUDMultiScatter"

class TemplateOptionsUVWG1DMulti(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: isofill, vector, boxfill and isoline.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = True
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = True
        self._line1          = False
        self._line2          = False
        self._line3          = True
        self._line4          = True
        self._logicalmask    = True
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False  # Still need to decide this one
        self._title          = True
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = True
        self._units          = True
        self._xlabel1        = True
        self._xlabel2        = False
        self._xmintic1       = True
        self._xmintic2       = False
        self._xname          = True
        self._xtic1          = True
        self._xtic2          = True
        self._xunits         = True
        self._xvalue         = True
        self._ylabel1        = True
        self._ylabel2        = False
        self._ymintic1       = True
        self._ymintic2       = False
        self._yname          = True
        self._ytic1          = True
        self._ytic2          = True
        self._yunits         = True
        self._yvalue         = True
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWG1DMulti"

class TemplateOptionsUVWG1DDUDMulti(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of type: isofill, vector, boxfill and isoline.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = False
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = True
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = False
        self._min            = False
        self._max            = False
        self._source         = False
        self._title          = False
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = False
        self._xlabel1        = False
        self._xlabel2        = False
        self._xmintic1       = False
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = False
        self._xtic2          = False
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = False
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = False
        self._ytic1          = False
        self._ytic2          = False
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWG1DDUDMulti"

class TemplateOptionsUVWGMulti_New(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of all types.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = True
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = False
        self._comment2       = False
        self._comment3       = False
        self._comment4       = False
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = True
        self._file           = False
        self._function       = False
        self._legend         = True
        self._line1          = False
        self._line2          = False
        self._line3          = True
        self._line4          = True
        self._logicalmask    = True
        self._mean           = True
        self._min            = True
        self._max            = True
        self._source         = False  # Still need to decide this one
        self._title          = True
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = True
        self._units          = True
        self._xlabel1        = True
        self._xlabel2        = False
        self._xmintic1       = True
        self._xmintic2       = False
        self._xname          = True
        self._xtic1          = True
        self._xtic2          = False
        self._xunits         = True
        self._xvalue         = True
        self._ylabel1        = True
        self._ylabel2        = False
        self._ymintic1       = True
        self._ymintic2       = False
        self._yname          = True
        self._ytic1          = True
        self._ytic2          = False
        self._yunits         = True
        self._yvalue         = True
        self._zname          = True
        self._zunits         = True
        self._zvalue         = True

        self.typeName = "TemplateOptionsUVWGMulti_New"

class TemplateOptionsUVWG(TemplateOptions):
    """
    Template Options Object for multiple plots on a page.
    This object is used for plots of all types.
    """
    def __init__(self):
        TemplateOptions.__init__(self)
        self._box1           = True
        self._box2           = False
        self._box3           = False
        self._box4           = False
        self._comment1       = True
        self._comment2       = True
        self._comment3       = True
        self._comment4       = True
        self._crdate         = False            
        self._crtime         = False
        self._data           = True
        self._dataname       = False
        self._file           = False
        self._function       = False
        self._legend         = True
        self._line1          = False
        self._line2          = False
        self._line3          = False
        self._line4          = False
        self._logicalmask    = False
        self._mean           = True
        self._min            = True
        self._max            = True
        self._source         = False
        self._title          = True
        self._tname          = False
        self._transformation = False   
        self._tunits         = False
        self._tvalue         = False
        self._units          = False
        self._xlabel1        = True
        self._xlabel2        = False
        self._xmintic1       = True
        self._xmintic2       = False
        self._xname          = False
        self._xtic1          = True
        self._xtic2          = True
        self._xunits         = False
        self._xvalue         = False
        self._ylabel1        = True
        self._ylabel2        = False
        self._ymintic1       = False
        self._ymintic2       = False
        self._yname          = True
        self._ytic1          = True
        self._ytic2          = True
        self._yunits         = False
        self._yvalue         = False
        self._zname          = False
        self._zunits         = False
        self._zvalue         = False

        self.typeName = "TemplateOptionsUVWG"
        
def setTemplateOptions(template, templateOptions):
    """
    This function enable/disable the template options given an object of
    type TemplateOptions.
    """
    if templateOptions.box1 is False:
        template.box1.priority = 0
    else:
        template.box1.priority = 1

    if templateOptions.box2 is False:
        template.box2.priority = 0
    else:
        template.box2.priority = 1
        
    if templateOptions.box3 is False:
        template.box3.priority = 0
    else:
        template.box3.priority = 1
        
    if templateOptions.box4 is False:
        template.box4.priority = 0
    else:
        template.box4.priority = 1
        
    if templateOptions.comment1 is False:
        template.comment1.priority = 0
    else:
        template.comment1.priority = 1

    if templateOptions.comment2 is False:
        template.comment2.priority = 0
    else:
        template.comment2.priority = 1

    if templateOptions.comment3 is False:
        template.comment3.priority = 0
    else:
        template.comment3.priority = 1

    if templateOptions.comment4 is False:
        template.comment4.priority = 0
    else:
        template.comment4.priority = 1
            
    if templateOptions.crdate is False:
        template.crdate.priority = 0
    else:
        template.crdate.priority = 1

    if templateOptions.crtime is False:
        template.crtime.priority = 0
    else:
        template.crtime.priority = 1

    if templateOptions.data is False:
        template.data.priority = 0
    else:
        template.data.priority = 1

    if templateOptions.dataname is False:
        template.dataname.priority = 0
    else:
        template.dataname.priority = 1
     
    if templateOptions.file is False:
        template.file.priority = 0
    else:
        template.file.priority = 1

    if templateOptions.function is False:
        template.function.priority = 0
    else:
        template.function.priority = 1

    if templateOptions.legend is False:
        template.legend.priority = 0
    else:
        template.legend.priority = 1
        
    if templateOptions.line1 is False:
        template.line1.priority = 0
    else:
        template.line1.priority = 1

    if templateOptions.line2 is False:
        template.line2.priority = 0
    else:
        template.line2.priority = 1

    if templateOptions.line3 is False:
        template.line3.priority = 0
    else:
        template.line3.priority = 1
    
    if templateOptions.line4 is False:
        template.line4.priority = 0
    else:
        template.line4.priority = 1

    if templateOptions.logicalmask is False:
        template.logicalmask.priority = 0
    else:
        template.logicalmask.priority = 1

    if templateOptions.mean is False:
        template.mean.priority = 0
    else:
        template.mean.priority = 1

    if templateOptions.min is False:
        template.min.priority = 0
    else:
        template.min.priority = 1

    if templateOptions.max is False:
        template.max.priority = 0
    else:
        template.max.priority = 1

    if templateOptions.source is False:
        template.source.priority = 0
    else:
        template.source.priority = 1

    if templateOptions.title is False:
        template.title.priority = 0
    else:
        template.title.priority = 1

    if templateOptions.tname is False:
        template.tname.priority = 0
    else:
        template.tname.priority = 1

    if templateOptions.transformation is False:
        template.transformation.priority = 0
    else:
        template.transformation.priority = 1

    if templateOptions.tunits is False:
        template.tunits.priority = 0
    else:
        template.tunits.priority = 1
        
    if templateOptions.tvalue is False:
        template.tvalue.priority = 0
    else:
        template.tvalue.priority = 1

    if templateOptions.units is False:
        template.units.priority = 0
    else:
        template.units.priority = 1

    if templateOptions.xlabel1 is False:
        template.xlabel1.priority = 0
    else:
        template.xlabel1.priority = 1

    if templateOptions.xlabel2 is False:
        template.xlabel2.priority = 0
    else:
        template.xlabel2.priority = 1

    if templateOptions.xmintic1 is False:
        template.xmintic1.priority = 0
    else:
        template.xmintic1.priority = 1
        
    if templateOptions.xmintic2 is False:
        template.xmintic2.priority = 0
    else:
        template.xmintic2.priority = 1

    if templateOptions.xname is False:
        template.xname.priority = 0
    else:
        template.xname.priority = 1

    if templateOptions.xtic1 is False:
        template.xtic1.priority = 0
    else:
        template.xtic1.priority = 1

    if templateOptions.xtic2 is False:
        template.xtic2.priority = 0
    else:
        template.xtic2.priority = 1

    if templateOptions.xunits is False:
        template.xunits.priority = 0
    else:
        template.xunits.priority = 1

    if templateOptions.xvalue is False:
        template.xvalue.priority = 0
    else:
        template.xvalue.priority = 1

    if templateOptions.ylabel1 is False:
        template.ylabel1.priority = 0
    else:
        template.ylabel1.priority = 1

    if templateOptions.ylabel2 is False:
        template.ylabel2.priority = 0
    else:
        template.ylabel2.priority = 1

    if templateOptions.ymintic1 is False:
        template.ymintic1.priority = 0
    else:
        template.ymintic1.priority = 1

    if templateOptions.ymintic2 is False:
        template.ymintic2.priority = 0
    else:
        template.ymintic2.priority = 1

    if templateOptions.yname is False:
        template.yname.priority = 0
    else:
        template.yname.priority = 1

    if templateOptions.ytic1 is False:
        template.ytic1.priority = 0
    else:
        template.ytic1.priority = 1

    if templateOptions.ytic2 is False:
        template.ytic2.priority = 0
    else:
        template.ytic2.priority = 1

    if templateOptions.yunits is False:
        template.yunits.priority = 0
    else:
        template.yunits.priority = 1

    if templateOptions.yvalue is False:
        template.yvalue.priority = 0
    else:
        template.yvalue.priority = 1
        
    if templateOptions.zname is False:
        template.zname.priority = 0
    else:
        template.zname.priority = 1
        
    if templateOptions.zunits is False:
        template.zunits.priority = 0
    else:
        template.zunits.priority = 1

    if templateOptions.zvalue is False:
        template.zvalue.priority = 0
    else:
        template.zvalue.priority = 1
