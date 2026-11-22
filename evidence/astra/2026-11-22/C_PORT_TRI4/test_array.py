"""Adversarial IEEE and array-wide exception probes; export words for comparison."""
import json
import numpy as np
from geoenclosereader.fiv import I
from cases_run import encode
cases=[
 ('sqrt_nan',lambda:I(np.array([1.,np.nan])).sqrt()),
 ('sq_nanlo',lambda:I(np.array([np.nan]),np.array([2.])).sq()),
 ('sq_nanhi',lambda:I(np.array([1.]),np.array([np.nan])).sq()),
 ('mul_nan',lambda:I(np.array([0.,np.nan]),np.array([1.,1.]))*I(np.inf)),
 ('sqrt_negative',lambda:I(np.array([1.,2.,-1.])).sqrt()),
 ('division_mixed',lambda:I(1.)/I(np.array([-2.,-1.,1.]))),
 ('division_zero',lambda:I(1.)/I(np.array([1.,2.,0.]))),
 ('division_negative',lambda:I(1.)/I(np.array([-1.,-2.]))),
]
def words(arr):
    return ['nan' if np.isnan(x) else encode(float(x)) for x in arr.ravel()]
with np.errstate(all='ignore'):
    for name,f in cases:
        try:
            v=f();o=[words(v.lo),words(v.hi)]
        except ValueError as e:o=[type(e).__name__,str(e)]
        print(json.dumps([name,o]))
