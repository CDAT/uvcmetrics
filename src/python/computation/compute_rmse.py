def compute_rmse(mv1, mv2):
    """compute rmse and correlations """
    import genutil.statistics, numpy
    RMSE = -numpy.infty
    CORR = -numpy.infty
    try:
        RMSE = float( genutil.statistics.rms(mv1, mv2, axis='xy') )
        CORR = float( genutil.statistics.correlation( mv1, mv2, axis='xy') )
    except Exception, err:
        pass
    return RMSE, CORR
