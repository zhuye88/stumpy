# STUMPY
# Copyright 2019 TD Ameritrade. Released under the terms of the 3-Clause BSD license.
# STUMPY is a trademark of TD Ameritrade IP Company, Inc. All rights reserved.

import math
import numpy as np
from .core import check_window_size
from .aampdist import _aampdist_vect


def _get_all_aampdist_profiles(
    T,
    m,
    percentage=1.0,
    s=None,
    mpdist_percentage=0.05,
    mpdist_k=None,
    mpdist_custom_func=None,
):
    """
    For each non-overlapping subsequence, `S[i]`, in `T`, compute the matrix profile
    distance measure vector between the `i`th non-overlapping subsequence and each
    sliding window subsequence, `T[j : j + m]`, within `T` where `j < len(T) - m + 1`.

    Parameters
    ----------
    T : ndarray
        The time series or sequence for which to find the snippets

    m : int
        The window size for each non-overlapping subsequence, `S[i]`.

    percentage : float, default 1.0
        With the length of each non-overlapping subsequence, `S[i]`, set to `m`, this
        is the percentage of `S[i]` (i.e., `percentage * m`) to set the `s` to. When
        `percentage == 1.0`, then the full length of `S[i]` is used to compute the
        `mpdist_vect`. When `percentage < 1.0`, then shorter subsequences from `S[i]`
        is used to compute `mpdist_vect`.

    s : int, default None
        With the length of each non-overlapping subsequence, `S[i]`, set to `m`, this
        is essentially the sub-subsequence length (i.e., a shorter part of `S[i]`).
        When `s == m`, then the full length of `S[i]` is used to compute the
        `mpdist_vect`. When `s < m`, then shorter subsequences with length `s` from
        each `S[i]` is used to compute `mpdist_vect`. When `s` is not `None`, then
        the `percentage` parameter is ignored.

    mpdist_percentage : float, default 0.05
        The percentage of distances that will be used to report `mpdist`. The value
        is between 0.0 and 1.0.

    mpdist_k : int
        Specify the `k`th value in the concatenated matrix profiles to return. When
        `mpdist_k` is not `None`, then the `mpdist_percentage` parameter is ignored.

    mpdist_custom_func : object, default None
        A custom user defined function for selecting the desired value from the
        sorted `P_ABBA` array. This function may need to leverage `functools.partial`
        and should take `P_ABBA` as its only input parameter and return a single
        `MPdist` value. The `percentage` and `k` parameters are ignored when
        `mpdist_custom_func` is not None.

    Returns
    -------
    D : ndarray
        MPdist profiles

    Notes
    -----
    `DOI: 10.1109/ICBK.2018.00058 \
    <https://www.cs.ucr.edu/~eamonn/Time_Series_Snippets_10pages.pdf>`__

    See Table II
    """
    if m > T.shape[0] // 2:  # pragma: no cover
        raise ValueError(
            f"The window size {m} for each non-overlapping subsequence is too large "
            f"for a time series with length {T.shape[0]}. "
            f"Please try `m <= len(T) // 2`."
        )

    right_pad = 0
    if T.shape[0] % m != 0:
        right_pad = int(m * np.ceil(T.shape[0] / m) - T.shape[0])
        pad_width = (0, right_pad)
        T = np.pad(T, pad_width, mode="constant", constant_values=np.nan)

    n_padded = T.shape[0]
    D = np.empty(((n_padded // m) - 1, n_padded - m + 1))

    if s is not None:
        s = min(int(s), m)
    else:
        percentage = min(percentage, 1.0)
        percentage = max(percentage, 0.0)
        s = min(math.ceil(percentage * m), m)

    # Iterate over non-overlapping subsequences, see Definition 3
    for i in range((n_padded // m) - 1):
        start = i * m
        stop = (i + 1) * m
        S_i = T[start:stop]
        D[i, :] = _aampdist_vect(
            S_i,
            T,
            s,
            percentage=mpdist_percentage,
            k=mpdist_k,
            custom_func=mpdist_custom_func,
        )

    stop_idx = n_padded - m + 1 - right_pad
    D = D[:, :stop_idx]

    return D


def aampdist_snippets(
    T,
    m,
    k,
    percentage=1.0,
    s=None,
    mpdist_percentage=0.05,
    mpdist_k=None,
):
    """
    Identify the top `k` snippets that best represent the time series, `T`

    Parameters
    ----------
    T : ndarray
        The time series or sequence for which to find the snippets

    m : int
        The snippet window size

    k : int
        The desired number of snippets

    percentage : float, default 1.0
        With the length of each non-overlapping subsequence, `S[i]`, set to `m`, this
        is the percentage of `S[i]` (i.e., `percentage * m`) to set the `s` to. When
        `percentage == 1.0`, then the full length of `S[i]` is used to compute the
        `mpdist_vect`. When `percentage < 1.0`, then shorter subsequences from `S[i]`
        is used to compute `mpdist_vect`.

    s : int, default None
        With the length of each non-overlapping subsequence, `S[i]`, set to `m`, this
        is essentially the sub-subsequence length (i.e., a shorter part of `S[i]`).
        When `s == m`, then the full length of `S[i]` is used to compute the
        `mpdist_vect`. When `s < m`, then shorter subsequences with length `s` from
        each `S[i]` is used to compute `mpdist_vect`. When `s` is not `None`, then
        the `percentage` parameter is ignored.

    mpdist_percentage : float, default 0.05
        The percentage of distances that will be used to report `mpdist`. The value
        is between 0.0 and 1.0.

    mpdist_k : int
        Specify the `k`th value in the concatenated matrix profiles to return. When
        `mpdist_k` is not `None`, then the `mpdist_percentage` parameter is ignored.

    Returns
    -------
    snippets : ndarray
        The top `k` snippets

    snippets_indices : ndarray
        The index locations for each of top `k` snippets

    snippets_profiles : ndarray
        The MPdist profiles for each of the top  `k` snippets

    snippets_fractions : ndarray
        The fraction of data that each of the top `k` snippets represents

    snippets_areas : ndarray
        The area under the curve corresponding to each profile for each of the top `k`
        snippets

    Notes
    -----
    `DOI: 10.1109/ICBK.2018.00058 \
    <https://www.cs.ucr.edu/~eamonn/Time_Series_Snippets_10pages.pdf>`__

    See Table I
    """
    if m > T.shape[0] // 2:  # pragma: no cover
        raise ValueError(
            f"The snippet window size of {m} is too large for a time series with "
            f"length {T.shape[0]}. Please try `m <= len(T) // 2`."
        )

    check_window_size(m, max_size=T.shape[0] // 2)

    D = _get_all_aampdist_profiles(
        T,
        m,
        percentage=percentage,
        s=s,
        mpdist_percentage=mpdist_percentage,
        mpdist_k=mpdist_k,
    )

    pad_width = (0, int(m * np.ceil(T.shape[0] / m) - T.shape[0]))
    T_padded = np.pad(T, pad_width, mode="constant", constant_values=np.nan)
    n_padded = T_padded.shape[0]

    snippets = np.empty((k, m))
    snippets_indices = np.empty(k, dtype=np.int64)
    snippets_profiles = np.empty((k, D.shape[-1]))
    snippets_fractions = np.empty(k)
    snippets_areas = np.empty(k)
    Q = np.full(D.shape[-1], np.inf)
    indices = np.arange(0, n_padded - m, m)

    for i in range(k):
        profile_areas = np.sum(np.minimum(D, Q), axis=1)
        idx = np.argmin(profile_areas)

        snippets[i] = T[indices[idx] : indices[idx] + m]
        snippets_indices[i] = indices[idx]
        snippets_profiles[i] = D[idx]
        snippets_areas[i] = np.sum(np.minimum(D[idx], Q))

        Q[:] = np.minimum(D[idx], Q)

    total_min = np.min(snippets_profiles, axis=0)

    for i in range(k):
        mask = snippets_profiles[i] <= total_min
        snippets_fractions[i] = np.sum(mask) / total_min.shape[0]
        total_min = total_min - mask.astype(float)

    return (
        snippets,
        snippets_indices,
        snippets_profiles,
        snippets_fractions,
        snippets_areas,
    )
