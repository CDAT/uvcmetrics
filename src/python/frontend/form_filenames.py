import logging, os
logger = logging.getLogger(__name__)
from metrics.common.utilities import underscore_join

def form_filename( rootname, fmt, descr='', vname='', more_id='' ):
    """This information goes into a file name computation, or possibly should go:
- root name, from form_file_rootname
- format of output (png,svg,pdf,nc).
- optional descriptive string for uniqueness, e.g. 'model' or 'obs1'.  The user can provides this, or True
  to have it computed here.  This differs from the postname which is used for the rootname computation.
  If descr is to be computed, we will need a cleaned-up variable name, vname:  descr is computed by
  extracting strings and making deductions from vname.
What this function returns depends on what fmt is.
  If a string (e.g. 'png'), we will return a full filename, and fmt will be the filename's suffix (e.g. foo.png).
  If a tuple of strings (e.g. 'png','svg'), we will will return the corresponding tuple of filenames.
  (e.g. foo.png,foo.svg)
"""
    if more_id is None: more_id=''
    if descr is not True:
        fnamedot = '-'.join([rootname,more_id,descr]) + '.'
        if type(fmt) is str:
            return fnamedot + fmt
        else:
            return tuple(fnamedot+fm for fm in fmt)

    # At this point descr==True: we should compute it.  For the moment however, I'm only
    # slightly modifying code moved from a former section of makeplots().

    #### TODO - Do we need the old style very verbose names here?
    #### jfp, my answer: The right way to do it is that all the verbose information
    #### useful for file names should be constructed elsewhere, perhaps in a named tuple.
    #### The verbose names are formed, basically, by concatenating everything in that
    #### tuple.  What we should do here is to form file names by concatenating the
    #### most interesting parts of that tuple, whatever they are.  But it's important
    #### to use enough so that different plots will almost surely have different names.
    #### bes - it is also a requirement that filenames be reconstructable after-the-fact
    #### with only the dataset name (the dsname parameter probably) and the combination of
    #### seasons/vars/setnames/varopts/etc used to create the plot. Otherwise, there is no
    #### way for classic viewer to know the filename without lots more special casing. 

    logger.debug("vname: %s", vname)
    # I *really* hate to do this. Filename should be handled better at a level above diags*.py
    # jfp: whoever wrote that is basically right.  Filenames should be computed in a separate file,
    # and whatever does i/o (should all be within frontend/) queries the functions there to get
    # filenames. (That much is implemented now.)  They should be based upon actual specifications
    # (e.g. season, obs filename); we shouldn't try to parse the specs out of lengthy ID strings.
    rootname='-'.join([rootname,more_id])
    special = ''
    if 'RMSE_' in vname:
        special='RMSE'
    if 'Standard_Deviation' in vname:
        special='STDDEV'
    if 'BIAS_' in vname:
        special='BIAS'
    if 'CORR_' in vname:
        special='CORR'
    if special != '':
        logger.debug('--> Special: %s', special)
        if ('_1' in vname and '_2' in vname) or '_MAP' in vname.upper():
            fnamedot = rootname+'-map.'
        elif '_1' in vname and '_2' not in vname:
            fnamedot = rootname+'-ds1.'
        elif '_2' in vname and '_1' not in vname:
            fnamedot = rootname+'-ds2.'
        elif '_0' in vname and '_1' not in vname:
            fnamedot = rootname+'-ds0.'
        else:
            logging.warning('Couldnt determine filename; defaulting to just .png. vname: %s, rootname: %s', vname, rootname)
            fnamedot = rootname+'.'
    elif '_diff' in vname or ' diff' in vname or "Difference" in vname or "difference" in vname or\
            ('_ft0_' in vname and '_ft1_' in vname) or ('_ft1_' in vname and '_ft2_' in vname):
        fnamedot = rootname+'-diff.'
    elif rootname[-9:]=='-combined':  # descr has really already been supplied by being stuck in the rootname
        fnamedot = rootname+'.'
    elif '_obs' in vname:
        fnamedot = rootname+'-obs.'
    else:
        if '_ttest' in vname:
            if 'ft1' in vname and 'ft2' in vname:
                #fnamedot = rootname+'-model1_model2_ttest.'
                fnamedot = rootname+'-model_obs_ttest.'
            elif 'ft1' in vname and 'ft2' not in vname:
                fnamedot = rootname+'-model1_ttest.'
            elif 'ft2' in vname and 'ft1' not in vname:
                #fnamedot = rootname+'-model2_ttest.'
                fnamedot = rootname+'-obs_ttest.'
        elif '_ft1' in vname and '_ft2' not in vname:
            fnamedot = rootname+'-model.'  
            # if we had switched to model1 it would affect classic view, etc.
        elif '_ft2' in vname and '_ft1' not in vname:
            #fnamedot = rootname+'-model2.'
            fnamedot = rootname+'-obs.'
        elif '_ft0' in vname and '_ft1' not in vname:
            fnamedot = rootname+'-model0.'
        elif '_ft1' in vname and '_ft2' in vname:
            #fnamedot = rootname+'-model-model2.'
            fnamedot = rootname+'-model-obs.'
        elif '_fts' in vname: # a special variable; typically like lmwg set3/6 or amwg set 2
            fnamedot = rootname+'_'+vname.replace('_fts','')+'.'
        else:
            logging.warning('Second spot - Couldnt determine filename; defaulting to just .png. vname: %s, rootname: %s', vname, rootname)
            fnamedot = rootname+'.'

    if type(fmt) is str:
        return fnamedot + fmt
    else:
        return tuple(fnamedot+fm for fm in fmt)


def form_file_rootname( plotset, vars, meanings='variable', dir='', filetables=[],
                   combined=False, season='ANN', basen='', postn='', aux=[], region='Global',
                   times=None ):
    """This information goes into a file root name computation, or possibly should go:
- plot set, a number, e.g. 5, or string, e.g. '4a'.  Or this could be a string identifying some special situation.
- combined or simple plot
- filetables (numbers, directory name, model/obs, etc.)
- season
- variable names (a name is a core name, e.g. TREFHT, not the extended IDs we use for dictionaries)
- user-provided basename, postname
- auxiliary parameters, e.g. level for a level set
- region
- time period (if there are time restrictions other than season; not implemented)
- user-specified directory (if the directory is considered to be part of the filename)
- output meaning: variable, diff, variance, rmse, etc.
"""
# For a first cut at this function, I will simply try to reproduce the present behavior.

    plotset = str(plotset)
    if plotset=='1':
        fname = 'table_output'
        return os.path.join( dir, fname )

    if plotset[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']: # i.e. [str(n) for n in range(10)]
        # This is a normal plotset.
        if basen == '' and postn == '':
            fname = underscore_join(['figure-set'+plotset, region, season, underscore_join(vars),
                                     'plot'])
        else:
            fname = underscore_join([ basen, season, underscore_join(vars), underscore_join(aux), postn ])
    elif plotset=='resstring':  # For "type(res) is str".
        if aux is None or aux==[None] or aux=='':
            aux = []
        fname = underscore_join([basen, season, underscore_join(vars), underscore_join(aux)]) + '-table.text'
    elif plotset=='res0':    # For len(res)==0
        fname = underscore_join([basen, season, region]) + '-table.text'

    return os.path.join( dir, fname )


