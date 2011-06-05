
from sqlalchemy import and_, or_

def tune_conds(tunes, cls):
    """Composite tunes to sql or condition.
    tunes=list of (music_id, dif_id) tuples
    """

    conds = []
    for music_id, dif_id in tunes:
        conds.append(and_(
            cls.music_id == music_id,
            cls.dif_id == dif_id))
    return or_(*conds)

def cutoff_dates(query, date_col, dates):
    start_date, end_date = dates
    if start_date is not None:
        query = query.filter(date_col >= start_date)
    if end_date is not None:
        query = query.filter(date_col <= end_date)
    return query

