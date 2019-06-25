import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

# The inupt image represents the 'true' sky intensity as a function of position
img = np.array(Image.open('data/hercules.png').convert("L"))


# Performing a 2D FFT on sky intensity will give us the complex visibilities.
# fftshift shifts the zero frequency components to the center of the image.
# Visibilities are also known as Coherence Functions.
vis_img = np.fft.fftshift(np.fft.fft2(img))
vis_img1 = np.copy(vis_img)
vis_img2 = np.copy(vis_img)
vis_img3 = np.copy(vis_img)

# Log transform enables us to view the large dynamic range of visibilities
vis_img_mag = np.log10(abs(vis_img))

# The coordinates of the center of image plane.
[x_0, y_0] = (np.array(np.shape(vis_img))/2).astype(np.int)
[x_m, y_m] = np.array(np.shape(vis_img)).astype(np.int)

array_latitude = 35
lat = np.radians(array_latitude)
# Reads array positions from array.csv file
# array-vla uses a n^(1.716) power law distribution like the real VLA
array = pd.read_csv('arrays/array-vla.csv')

# X,Y coordinates of tiles.
E = np.array(list(array.E))
N = np.array(list(array.N))

# The array positions are defined in a tangent plane at the location of the array center.
# Bases on the latitude of the array, we transform the (E,N) coordinates to an ECEF (x,y,z) coordinates.
x = -np.sin(lat)*N
y = E
z = np.cos(lat)*N


# UV sampling function depends on sampling of uv space by baselines.
# The baseline for every antenna w.r.t every other antenna is determined
# This code is equivalent to two nested for loops
lx = np.concatenate(x - x[:, None])
ly = np.concatenate(y - y[:, None])
lz = np.concatenate(z - z[:, None])


# As the Earth rotates, projection of the array increases UV coverage. This is known as rotation synthesis
# Hour angle changes though the observation period due to the Earth's Rotation
# This leads to the formation of elliptical  UV tracks.

# Interval of consecutive observations in seconds
cadence = 120
# Angle interval between observations in Radians
angle_int = cadence*((2*np.pi)/(24*60*60))

obs_t = 8  # Total time of observation in hours
obs_time = obs_t*3600  # Total time of observation converted to seconds
n_obs = int(round(obs_time/cadence))  # Number of individual observations

declination = 45  # Decliantion of the phase center of the source, in degrees
dec = np.radians(declination)  # Concert to radians

init_hour = -(obs_t/2)  # Initial hour angle in hours
h_0 = np.radians(init_hour*15)  # Initial hour angle in radians

# List of Hour angle positions for each snapshot
h = np.array(np.arange(n_obs))*angle_int + h_0

# The xyz matrix represents the position of each baseline.
# Each column of this matrix represents an individual baseline of the array.
xyz = np.array(np.vstack((lx, ly, lz)))
uvw = np.empty((3, 0))

# The transformation matrix 't' depends on the declination 'dec' of the source.
# It also depends on the Hour angle of the sourse in the sky. As the source
# drifts along the sky, the matrix t changes. Each of these unique t matrices
# is multiplied by xyz matrix to form ellipses in the uv plane.
for j in range(len(h)):
    t = np.array([[np.sin(h[j]),
                   np.cos(h[j]),
                   0],
                  [-np.sin(dec)*np.cos(h[j]),
                   np.sin(dec)*np.sin(h[j]),
                   np.cos(dec)],
                  [np.cos(dec)*np.cos(h[j]),
                   -np.cos(dec)*np.sin(h[j]),
                   np.sin(dec)]])
    uv_ellipse = (np.dot(t, xyz))
    uvw = np.c_[uvw, uv_ellipse]

u_rot = np.array(uvw[0]).ravel()
v_rot = np.array(uvw[1]).ravel()

# Wavelength dependent beam shape

wavelength = (1.0, 1.2, 1.6, 2.0, 2.4, 2.8)

images = []
uv_lambda = []

for i in wavelength:
    uvw_lambda = (1/i)*uvw
    u_lambda = np.array(uvw_lambda[0]).ravel()
    v_lambda = np.array(uvw_lambda[1]).ravel()
    mask_l = np.zeros(np.shape(vis_img3))
    mask_l[(np.around(v_lambda).astype(np.int)+y_0,
            np.around(u_lambda).astype(np.int)+x_0)] = 1

    img_l = np.multiply(vis_img3, mask_l)
    images.append(abs(np.fft.ifft2(np.fft.fftshift(img_l))))

    uv = [u_lambda, v_lambda]
    uv_lambda.append(uv)


# Mask to sample visibilites
mask = np.zeros(np.shape(vis_img))
mask[np.around(lx).astype(np.int)+x_0,
     np.around(ly).astype(np.int)+y_0] = 1
dirty_img = abs(np.fft.ifft2(np.fft.fftshift(np.multiply(vis_img1, mask))))

# Mask of Rotation Synthesis
mask_rot = np.zeros(np.shape(vis_img))
mask_rot[np.around(u_rot).astype(np.int)+x_0,
         np.around(v_rot).astype(np.int)+y_0] = 1
dirty_img_rot = abs(np.fft.ifft2(np.fft.fftshift(np.multiply(vis_img2,
                                                             mask_rot))))


# Plotting images
plt.style.use('dark_background')

# # Plots of UV coverage as a fuction of wavelength
# fig, ((ax0, ax1, ax2), (ax3, ax4, ax5)) = plt.subplots(2, 3, figsize=(14, 7))

# ax0.plot(uv_lambda[0][0], uv_lambda[0][1], ',', color='white')
# ax0.set_title('Lambda =' + str(wavelength[0]))
# ax0.set_xlim([-256, 256])
# ax0.set_ylim([-256, 256])
# ax0.set_aspect('equal')


# ax1.plot(uv_lambda[1][0], uv_lambda[1][1], ',', color='white')
# ax1.set_title('Lambda =' + str(wavelength[1]))
# ax1.set_xlim([-256, 256])
# ax1.set_ylim([-256, 256])
# ax1.set_aspect('equal')


# ax2.plot(uv_lambda[2][0], uv_lambda[2][1], ',', color='white')
# ax2.set_title('Lambda =' + str(wavelength[2]))
# ax2.set_xlim([-256, 256])
# ax2.set_ylim([-256, 256])
# ax2.set_aspect('equal')


# ax3.plot(uv_lambda[3][0], uv_lambda[3][1], ',', color='white')
# ax3.set_title('lambda =' + str(wavelength[3]))
# ax3.set_xlim([-256, 256])
# ax3.set_ylim([-256, 256])
# ax3.set_aspect('equal')


# ax4.plot(uv_lambda[4][0], uv_lambda[4][1], ',', color='white')
# ax4.set_title('Lambda =' + str(wavelength[4]))
# ax4.set_xlim([-256, 256])
# ax4.set_ylim([-256, 256])
# ax4.set_aspect('equal')


# ax5.plot(uv_lambda[5][0], uv_lambda[5][1], ',', color='white')
# ax5.set_title('Lambda =' + str(wavelength[5]))
# ax5.set_xlim([-256, 256])
# ax5.set_ylim([-256, 256])
# ax5.set_aspect('equal')

# fig.tight_layout()


# # Plots of dirty images (Snapshots, not rotation) as a function of wavelength.
# fig, ((ax0, ax1, ax2), (ax3, ax4, ax5)) = plt.subplots(2, 3, figsize=(14, 7))

# im0 = ax0.imshow(images[0], cmap='magma')
# ax0.set_title('Lambda =' + str(wavelength[0]))
# ax0.set_aspect('equal')
# cbar0 = plt.colorbar(im0, ax=ax0)

# im1 = ax1.imshow(images[1], cmap='magma')
# ax1.set_title('Lambda =' + str(wavelength[1]))
# ax1.set_aspect('equal')
# cbar1 = plt.colorbar(im1, ax=ax1)

# im2 = ax2.imshow(images[2], cmap='magma')
# ax2.set_title('Lambda =' + str(wavelength[2]))
# ax2.set_aspect('equal')
# cbar2 = plt.colorbar(im2, ax=ax2)

# im3 = ax3.imshow(images[3], cmap='magma')
# ax3.set_title('lambda =' + str(wavelength[3]))
# ax3.set_aspect('equal')
# cbar3 = plt.colorbar(im3, ax=ax3)

# im4 = ax4.imshow(images[4], cmap='magma')
# ax4.set_title('Lambda =' + str(wavelength[4]))
# ax4.set_aspect('equal')
# cbar4 = plt.colorbar(im4, ax=ax4)

# im5 = ax5.imshow(images[5], cmap='magma')
# ax5.set_title('Lambda =' + str(wavelength[5]))
# ax5.set_aspect('equal')
# cbar5 = plt.colorbar(im5, ax=ax5)

# fig.tight_layout()


# Plots of dirty image with and without rotation synthesis.
fig, ((ax3, ax4)) = plt.subplots(1, 2, figsize=(11, 4))

im3 = ax3.imshow(dirty_img, cmap='magma')
ax3.set_title('Dirty Image')
ax3.set_aspect('equal')
cbar3 = plt.colorbar(im3, ax=ax3)
im4 = ax4.imshow(dirty_img_rot, cmap='magma')
ax4.set_title('Dirty Image + Rotation Synthesis')
ax4.set_aspect('equal')
cbar4 = plt.colorbar(im4, ax=ax4)
fig.tight_layout()


# Plots of original data and visibilities.
fig, ((ax1, ax2)) = plt.subplots(1, 2, figsize=(11, 4))

im1 = ax1.imshow(img, cmap='magma')
ax1.set_title('Hercules A')
ax1.set_aspect('equal')
cbar1 = plt.colorbar(im1, ax=ax1)
im2 = ax2.imshow(vis_img_mag, cmap='magma')
ax2.set_title('Visibility Amplitudes')
ax2.set_aspect('equal')
cbar2 = plt.colorbar(im2, ax=ax2)
fig.tight_layout()

# # Plots of array configurations and UV sampling with and without rotation.
fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))


ax1.plot(array.E, array.N, ',', color='white')
ax1.set_title('Array Configuraton')
ax1.set_aspect('equal')
ax1.set_xlim((-x_0/2, x_0/2))
ax1.set_ylim((-y_0/2, y_0/2))
ax2.plot(np.concatenate(E - E[:, None]),
         np.concatenate(N - N[:, None]), ',', color='white')
ax2.set_title('$UV$ Snapshot')
ax2.set_aspect('equal')
ax2.set_xlim((-x_0, x_0))
ax2.set_ylim((-y_0, y_0))
ax3.plot(u_rot, v_rot, ',', color='white')
ax3.set_title('$UV$ Rotation Synthesis')
ax3.set_aspect('equal')
ax3.set_xlim((-x_0, x_0))
ax3.set_ylim((-y_0, y_0))
fig.tight_layout()

plt.show()
