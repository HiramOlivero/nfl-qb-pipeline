import logging
import polars as pl


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger


OFFICIAL_PASS = (
        (pl.col('sack').cast(pl.Int8) == 0) &
        (pl.col('fumble').cast(pl.Int8) == 0) &
        (pl.col('two_point_conv_result').is_null())
)

PRESSURE_TYPE = (
    pl.when(pl.col('qb_hit') == 1)
    .then(pl.lit('hit'))
    .when(pl.col('qb_scramble') == 1)
    .then(pl.lit('scramble'))
    .otherwise(pl.lit('clean'))
    .alias('pressure_type')

)
