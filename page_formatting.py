import pandas as pd

def gbp(x, dp=0):
    """Format a value as GBP."""
    if pd.isna(x):
        return ""

    x = float(x)
    sign = "-" if x < 0 else ""

    return f"{sign}£{abs(x):,.{dp}f}"