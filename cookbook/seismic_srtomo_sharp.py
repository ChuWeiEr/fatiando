"""
Seismic: 2D straight-ray tomography using sharpness (total variation)
regularization
"""
import numpy as np
from fatiando.mesher import SquareMesh
from fatiando.seismic import ttime2d, srtomo
from fatiando.inversion.regularization import TotalVariation2D, LCurve
from fatiando.vis import mpl
from fatiando import utils

area = (0, 500000, 0, 500000)
shape = (30, 30)
model = SquareMesh(area, shape)
vel =  4000*np.ones(shape)
vel[5:25, 5:25] = 10000
model.addprop('vp', vel.ravel())

# Make some travel time data and add noise
seed = 0 # Set the random seed so that points are the same everythime
src_loc = utils.random_points(area, 80, seed=seed)
rec_loc = utils.circular_points(area, 30, random=True, seed=seed)
srcs, recs = utils.connect_points(src_loc, rec_loc)
tts = ttime2d.straight(model, 'vp', srcs, recs)
tts, error = utils.contaminate(tts, 0.02, percent=True, return_stddev=True,
                               seed=seed)
# Make the mesh
mesh = SquareMesh(area, shape)
# and run the inversion
misfit = srtomo.SRTomo(tts, srcs, recs, mesh)
regularization = TotalVariation2D(10**-10, mesh.shape)
tomo = misfit + regularization
tomo = LCurve(misfit, regularization,
              [10**i for i in np.arange(-3, 3, 0.5)])
# Since Total Variation is a non-linear function, then the tomography becomes
# non-linear. So we need to configure fit to use the Levemberg-Marquardt
# algorithm, a gradient descent method, that requires an initial estimate
tomo.config('levmarq', initial=0.00001*np.ones(mesh.size)).fit()
mesh.addprop('vp', tomo.estimate_)

# Plot the L-curve annd print the regularization parameter estimated
mpl.figure()
mpl.title('L-curve: triangle marks the best solution')
tomo.plot_lcurve()
print "Estimated regularization parameter: %g" % (tomo.regul_param_)

# Calculate and print the standard deviation of the residuals
# Should be close to the data error if the inversion was able to fit the data
residuals = tomo.residuals()
print "Assumed error: %f" % (error)
print "Standard deviation of residuals: %f" % (np.std(residuals))

mpl.figure(figsize=(14, 5))
mpl.subplot(1, 2, 1)
mpl.axis('scaled')
mpl.title('Vp model')
mpl.squaremesh(model, prop='vp', vmin=4000, vmax=10000,
    cmap=mpl.cm.seismic)
cb = mpl.colorbar()
cb.set_label('Velocity')
mpl.points(src_loc, '*y', label="Sources")
mpl.points(rec_loc, '^r', label="Receivers")
mpl.legend(loc='lower left', shadow=True, numpoints=1, prop={'size':10})
mpl.m2km()
mpl.subplot(1, 2, 2)
mpl.axis('scaled')
mpl.title('Tomography result')
mpl.squaremesh(mesh, prop='vp', vmin=4000, vmax=10000,
    cmap=mpl.cm.seismic)
cb = mpl.colorbar()
cb.set_label('Velocity')
mpl.m2km()
mpl.figure()
mpl.grid()
mpl.title('Residuals (data with %.4f s error)' % (error))
mpl.hist(residuals, color='gray', bins=10)
mpl.xlabel("seconds")
mpl.show()
