def compute_rmse(mv1, mv2):
    """compute rmse and correlations """
    import genutil.statistics, numpy, cdutil
    RMSE = -numpy.infty
    CORR = -numpy.infty
    try:
        weights = cdutil.area_weights(mv1)
        RMSE = float( genutil.statistics.rms(mv1, mv2, axis='xy', weights=weights) )
        CORR = float( genutil.statistics.correlation( mv1, mv2, axis='xy', weights=weights) )
    except Exception, err:
        pass
    return RMSE, CORR
