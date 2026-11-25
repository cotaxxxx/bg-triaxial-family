"""Check the design's algebra on fixed, small rational fixtures."""

from fractions import Fraction as F
from itertools import product


UNIT_CORNERS = tuple((F(u), F(v)) for v, u in product(range(2), repeat=2))


def quadratic_value(coefficients, u, v):
    c, cu, cv, cuu, cuv, cvv = coefficients
    return c + cu * u + cv * v + cuu * u**2 + cuv * u * v + cvv * v**2


def quadratic_extrema(coefficients):
    """Return exact extrema of (1, u, v, u², uv, v²) on the unit square."""
    _, cu, cv, cuu, cuv, cvv = coefficients
    candidates = list(UNIT_CORNERS)
    for fixed in (F(0), F(1)):
        if cuu:
            u = -(cu + cuv * fixed) / (2 * cuu)
            if 0 < u < 1:
                candidates.append((u, fixed))
        if cvv:
            v = -(cv + cuv * fixed) / (2 * cvv)
            if 0 < v < 1:
                candidates.append((fixed, v))

    determinant = 4 * cuu * cvv - cuv**2
    if determinant:
        u = (cuv * cv - 2 * cvv * cu) / determinant
        v = (cuv * cu - 2 * cuu * cv) / determinant
        if 0 < u < 1 and 0 < v < 1:
            candidates.append((u, v))
    values = [quadratic_value(coefficients, u, v) for u, v in candidates]
    return min(values), max(values)


def interpolation_coefficients(corner_values, s_curvature, t_curvature, ds, dt):
    c00, c10, c01, c11 = corner_values
    first = ds**2 * s_curvature / 2
    second = dt**2 * t_curvature / 2
    return (c00, c10 - c00 - first, c01 - c00 - second, first,
            c11 - c10 - c01 + c00, second)


def shape_bounds(corners, ks, kt, ds, dt, position):
    lower = interpolation_coefficients([c[0] for c in corners], ks[1], kt[1], ds, dt)
    upper = interpolation_coefficients([c[1] for c in corners], ks[0], kt[0], ds, dt)
    return (quadratic_extrema(lower)[0] + position[0],
            quadratic_extrema(upper)[1] + position[1])


def check_interpolation():
    def bowl(u, v):
        x, y = u - F(1, 2), v - F(1, 2)
        return F(1, 8) + x**2 + y**2 + x * y

    error = F(1, 64)
    corners = [(bowl(u, v) - error, bowl(u, v) + error) for u, v in UNIT_CORNERS]
    position = (-error, error)
    with_extrema = shape_bounds(corners, (F(2), F(2)), (F(2), F(2)), F(1), F(1),
                               position)
    independent = (min(c[0] for c in corners) - F(1, 2) + position[0],
                   max(c[1] for c in corners) + position[1])
    assert with_extrema == (F(3, 32), F(29, 32))
    assert independent == (F(-5, 32), F(29, 32))
    grid = [F(i, 16) for i in range(17)]
    for u, v, p in product(grid, grid, position):
        assert with_extrema[0] <= bowl(u, v) + p <= with_extrema[1]
    print(f"Positive quadratic fixture: [{with_extrema[0]}, {with_extrema[1]}]")
    print(f"Independent remainder hull: [{independent[0]}, {independent[1]}]")

    def cubic(u, v):
        return u**3 - 2 * v**3 + u * v

    # The physical shape widths are 2 and 3, while u and v are normalized.
    corners = [(cubic(u, v), cubic(u, v)) for u, v in UNIT_CORNERS]
    lower, upper = shape_bounds(corners, (F(0), F(6, 4)), (F(-12, 9), F(0)),
                                F(2), F(3), (F(0), F(0)))
    assert (lower, upper) == (F(-25, 12), F(49, 24))
    for u, v in product(grid, repeat=2):
        assert lower <= cubic(u, v) <= upper
    print(f"Opposite signed curvatures and unequal widths: [{lower}, {upper}]")

    degenerate = [(1 + v**2, 1 + v**2) for _, v in UNIT_CORNERS]
    assert shape_bounds(degenerate, (F(0), F(0)), (F(2), F(2)), F(0), F(1),
                        (F(0), F(0))) == (F(1), F(2))
    print("Zero shape width: [1, 2]")


def check_quadratic_extrema():
    # Rank one with a line of minima, a saddle, and an affine edge with no root.
    fixtures = (
        ((1, -2, -4, 1, 4, 4), (0, 4)),
        ((F(-1, 3), F(-2, 3), F(4, 3), 1, 0, -1), (F(-4, 9), F(4, 9))),
        ((3, 2, 0, 0, 0, 0), (3, 5)),
    )
    for coefficients, expected in fixtures:
        assert quadratic_extrema(tuple(map(F, coefficients))) == expected
    print("Quadratic extrema: rank one [0, 4], saddle [-4/9, 4/9], affine [3, 5]")


def check_shape_derivatives():
    xi = (F(1, 3), F(2, 3), F(2, 3))
    q = (F(1, 11), F(1, 13), F(1, 17))
    s, t = F(7, 5), F(9, 7)
    x = tuple((e - p)**2 for e, p in zip(xi, q))
    y = tuple(e**2 for e in xi)
    k = 1 - sum(e * p for e, p in zip(xi, q))
    w = (F(1), s**2, s**2 * t**2)
    exponents = ((0, 2, 2), (0, 0, 2))
    assert sum(y) == 1 and sum(p**2 for p in q) < 1

    for name, sigma, axis_exponents in zip(("s", "t"), (s, t), exponents):
        groups = {-2: F(0), 0: F(0), 2: F(0)}
        for i, j in product(range(3), repeat=2):
            groups[axis_exponents[i] - axis_exponents[j]] += x[i] * y[j] * w[i] / w[j]
        p = sum(groups.values())
        dp = 2 * (groups[2] - groups[-2]) / sigma
        ddp = (2 * groups[2] + 6 * groups[-2]) / sigma**2

        # Differentiate the two factors separately, then use the product rule.
        d2 = sum(wi * xi2 for wi, xi2 in zip(w, x))
        b2 = sum(yi2 / wi for wi, yi2 in zip(w, y))
        dd2 = sum(e * wi * xi2 for e, wi, xi2 in zip(axis_exponents, w, x)) / sigma
        db2 = sum(-e * yi2 / wi for e, wi, yi2 in zip(axis_exponents, w, y)) / sigma
        ddd2 = sum(e * (e - 1) * wi * xi2
                   for e, wi, xi2 in zip(axis_exponents, w, x)) / sigma**2
        ddb2 = sum(e * (e + 1) * yi2 / wi
                   for e, wi, yi2 in zip(axis_exponents, w, y)) / sigma**2
        assert (p, dp, ddp) == (d2 * b2, dd2 * b2 + d2 * db2,
                                ddd2 * b2 + 2 * dd2 * db2 + d2 * ddb2)

        a_normalized, b_normalized = sigma * dp / p, sigma**2 * ddp / p
        assert -2 <= a_normalized <= 2 and 0 <= b_normalized <= 6
        x_ratio = (groups[2] - groups[-2]) / p
        y_ratio = (groups[2] + groups[-2]) / p
        curvature = F(3, 4) * a_normalized**2 - b_normalized / 2
        assert abs(x_ratio) <= y_ratio <= 1
        assert curvature == 3 * x_ratio**2 + x_ratio - 2 * y_ratio
        assert F(-25, 12) <= curvature <= 2
        # With the artificial F(gamma) = gamma², both forms are rational.
        chain = (k**2 / p) * (a_normalized**2 / 2 + 2 * curvature) / sigma**2
        direct = k**2 * (2 * dp**2 / p**3 - ddp / p**2)
        assert chain == direct
        print(f"{name} direction: P, P', P'', normalized bounds and chain rule agree exactly")

    for x_ratio, y_ratio, expected in ((F(-1, 6), F(1), F(-25, 12)),
                                        (F(1), F(1), F(2))):
        assert 3 * x_ratio**2 + x_ratio - 2 * y_ratio == expected
    print("Shape factor on the synthetic triangle: boundary values -25/12 and 2")


def main():
    print("DIAGNOSTIC_ONLY. Synthetic rational fixtures, no numerical H33 evaluations.")
    check_interpolation()
    check_quadratic_extrema()
    check_shape_derivatives()


if __name__ == "__main__":
    main()
