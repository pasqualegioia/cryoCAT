from cryocat import cryomap
import numpy as np
import pandas as pd
from cryocat import mdoc
from cryocat import ioutils
from skimage.transform import downscale_local_mean
from skimage import exposure
import warnings
from functools import wraps


def suppress_warnings(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            result = func(*args, **kwargs)
        return result

    return wrapper


def bin(tilt_stack, binning_factor):

    # binned_stack = np.zeros((tilt_stack.shape[0],tilt_stack.shape[1],tilt_stack.shape[0]

    # for z in range(tilt_stack.shape[0]):

    #    binned_stack[z, :, :] = downscale_local_mean(tilt_stack[z, :, :], (1, binning_factor, binning_factor))

    binned_stack = downscale_local_mean(tilt_stack, (1, binning_factor, binning_factor))
    print(tilt_stack.dtype)
    return binned_stack.astype(tilt_stack.dtype)


def equalize_histogram(tilt_stack, eh_method="contrast_stretching"):

    equalized_titls = np.zeros(tilt_stack.shape)

    for z in range(tilt_stack.shape[0]):
        if eh_method == "contrast_stretching":
            p2, p98 = np.percentile(tilt_stack[z, :, :], (2, 98))
            equalized_titls[z, :, :] = exposure.rescale_intensity(tilt_stack[z, :, :], in_range=(p2, p98))
        elif eh_method == "equalization":
            # Equalization
            equalized_titls[z, :, :] = exposure.equalize_hist(tilt_stack[z, :, :])
        elif eh_method == "adaptive_eq":
            # Adaptive Equalization
            equalized_titls[z, :, :] = exposure.equalize_adapthist(tilt_stack[z, :, :], clip_limit=0.03)
        else:
            raise ValueError(f"The {eh_method} is not known!")

    return equalized_titls.astype(tilt_stack.dtype)


def calculate_total_dose_batch(tomo_list, prior_dose_file_format, dose_per_image, output_file_format):
    tomograms = ioutils.tlt_load(tomo_list).astype(int)

    for t in tomograms:
        file_name = ioutils.fileformat_replace_pattern(prior_dose_file_format, t, "x", raise_error=False)
        total_dose = calculate_total_dose(file_name, dose_per_image)
        output_file = ioutils.fileformat_replace_pattern(output_file_format, t, "x", raise_error=False)
        np.savetxt(output_file, total_dose, fmt="%.6f")


def calculate_total_dose(prior_dose, dose_per_image):
    prior_dose = ioutils.total_dose_load(prior_dose)
    total_dose = prior_dose + dose_per_image

    return total_dose


def dose_filter(mrc_file, pixel_size, total_dose, output_file=None, return_data_order="xyz"):
    # Input: mrc_file or path to it
    #        pixelsize: float, in Angstroms
    #        total_dose: ndarray or path to the .csv, .txt, or .mdoc file
    #        return_data_order: by default x y z (x,y,n_tilts), for napari compatible view use "zyx"

    # temporarily here until this function exist as an entry point on command line
    pixel_size = float(pixel_size)

    stack_data = cryomap.read(mrc_file)
    total_dose = ioutils.total_dose_load(total_dose)

    imgs_x = stack_data.shape[0]
    imgs_y = stack_data.shape[1]
    n_tilt_imgs = stack_data.shape[2]

    # Precalculate frequency array
    frequency_array = np.zeros((imgs_x, imgs_y))
    cen_x = imgs_x // 2  # Center for array is half the image size
    cen_y = imgs_y // 2  # Center for array is half the image size

    rstep_x = 1 / (imgs_x * pixel_size)  # reciprocal pixel size
    rstep_y = 1 / (imgs_y * pixel_size)

    # Loop to fill array with frequency values
    for x in range(imgs_x):
        for y in range(imgs_y):
            d = np.sqrt(((x - cen_x) ** 2 * rstep_x**2) + ((y - cen_y) ** 2 * rstep_y**2))
            frequency_array[x, y] = d

    # Generate filtered stack
    filtered_stack = np.zeros((imgs_x, imgs_y, n_tilt_imgs), dtype=np.single)
    for i in range(n_tilt_imgs):
        image = stack_data[:, :, i]
        filtered_stack[:, :, i] = dose_filter_single_image(image, total_dose[i], frequency_array)

    if return_data_order == "zyx":
        filtered_stack = filtered_stack.transpose(2, 1, 0)

    if output_file is not None:
        cryomap.write(filtered_stack, output_file)

    return filtered_stack


@suppress_warnings
def dose_filter_single_image(image, dose, freq_array):
    # Hard-coded resolution-dependent critical exposures
    # These parameters come from the fitted numbers in the Grant and Grigorieff paper.
    a = 0.245
    b = -1.665
    c = 2.81

    # Calculate Fourier transform
    ft = np.fft.fftshift(np.fft.fft2(image))

    # Calculate exposure-dependent amplitude attenuator
    q = np.exp((-dose) / (2 * ((a * (freq_array**b)) + c)))

    # Attenuate and inverse transform
    filtered_image = np.fft.ifft2(np.fft.ifftshift(ft * q))

    return filtered_image.real


def deconvolve(
    tilt_stack,
    pixel_size_a,
    defocus,
    defocus_file_type="gctf",
    snr_falloff=1.2,
    deconv_strength=1.0,
    highpass_nyquist=0.02,
    phase_flipped=False,
    phaseshift=0,
    output_name=None,
):
    """Deconvolution adapted from MATLAB script tom_deconv_tomo by D. Tegunov (https://github.com/dtegunov/tom_deconv)
    and adapted for the tilt series.
    Example for usage: deconvolve(my_map, 3.42, 6, 1.1, 1, 0.02, false, 0)

    Parameters
    ----------
    tilt_stack : np.array or string
        tilt stack
    pixel_size_a : float
        pixel size in Angstroms
    defocus : float, int, str or array-like
        defocus in micrometers, positive = underfocus, or file from CTF estimation
    defocus_file_type : str, default=gctf
        in case the defocus is specified as a file, the type of the file has to be specified (ctffind4, gctf, warp)
    snr_falloff : float
        how fast does SNR fall off, i. e. higher values will downweight high frequencies; values like 1.0 or 1.2 seem reasonable
    deconv_strength : float
        how much will the signal be deconvoluted overall, i. e. a global scale for SNR; exponential scale: 1.0 is SNR = 1000 at zero frequency, 0.67 is SNR = 100, and so on
    highpass_nyquist : float
        fraction of Nyquist frequency to be cut off on the lower end (since it will be boosted the most)
    phase_flipped : bool
        whether the data are already phase-flipped. Defaults to False.
    phaseshift : int
        CTF phase shift in degrees (e. g. from a phase plate). Defaults to 0.
    output_name : str
        Name of the output file for the deconvolved stack. Defaults to None (tilt stack will be not written).

    Returns
    -------
    deconvolved_stack : np.array
        deconvolved tilt stack

    """
    input_stack = cryomap.read(tilt_stack, transpose=False)
    deconvolved_stack = np.zeros(input_stack.shape)

    if not isinstance(defocus, (int, float)):
        defocus = ioutils.defocus_load(defocus, defocus_file_type)
        defocus = defocus["defocus_mean"].values
    else:
        defocus = np.full((input_stack.shape[0],), defocus)

    for ts in range(input_stack.shape[0]):
        tilt = input_stack[ts, :, :]
        interp_dim = np.maximum(2048, tilt.shape[0])

        # Generate highpass filter
        highpass = np.arange(0, 1, 1 / interp_dim)
        highpass = np.minimum(1, highpass / highpass_nyquist) * np.pi
        highpass = 1 - np.cos(highpass)

        # Calculate SNR and Wiener filter
        snr = (
            np.exp(np.arange(0, -1, -1 / interp_dim) * snr_falloff * 100 / pixel_size_a)
            * (10 ** (3 * deconv_strength))
            * highpass
        )
        ctf = cryomap.compute_ctf_1d(
            interp_dim,
            pixel_size_a * 1e-10,
            300e3,
            2.7e-3,
            -defocus[ts] * 1e-6,
            0.07,
            phaseshift / 180 * np.pi,
            0,
        )
        if phase_flipped:
            ctf = np.abs(ctf)
        wiener = ctf / (ctf * ctf + 1 / snr)

        # Generate ramp filter
        s = tilt.shape
        x, y = np.meshgrid(
            np.arange(-s[0] / 2, s[0] / 2),
            np.arange(-s[1] / 2, s[1] / 2),
            indexing="ij",
        )

        x /= abs(s[0] / 2)
        y /= abs(s[1] / 2)
        r = np.sqrt(x * x + y * y)
        r = np.minimum(1, r)
        r = np.fft.ifftshift(r)

        x = np.arange(0, 1, 1 / interp_dim)
        ramp_interp = cryomap.interp1d(x, wiener, fill_value="extrapolate")

        ramp = ramp_interp(r.flatten()).reshape(r.shape)
        # Perform deconvolution
        deconvolved_stack[ts, :, :] = np.real(np.fft.ifftn(np.fft.fftn(tilt) * ramp))

    if output_name is not None:
        cryomap.write(deconvolved_stack, output_name, data_type=np.single, transpose=False)

    return deconvolved_stack


def split_stack_even_odd(tilt_stack):
    even_stack = []
    odd_stack = []

    # For each tilt image in the stack
    for i in range(0, tilt_stack.shape[2]):

        # Split to even and odd by using modulo 2
        if i % 2 == 0:
            even_stack.append(tilt_stack[:,:,i])
        else:
            odd_stack.append(tilt_stack[:,:,i])

    # Stack separated tilts together into one volume
    even_stack = np.stack(even_stack, axis=2)
    odd_stack = np.stack(odd_stack, axis=2)

    return even_stack, odd_stack