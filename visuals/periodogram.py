import temp_plots as tp
import scipy.signal as sig
import matplotlib.pyplot as plt
import numpy as np

t = tp.time_array_epoch
t = (t - t[0]) / (60*60*24) # Time passed in days
y = tp.temp_array
y = y - np.mean(y)

N_samples = len(t)
max_daily_freq = 4 # At most 4 times a day (sampling rate)
max_daily_period = 10 # A period of at most 10 days

# Lomb-scargle power spectrum: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lombscargle.html\n

f_angular =  np.linspace(1/(max_daily_period*2*np.pi), max_daily_freq*2*np.pi, N_samples)
f_daily = f_angular / (2*np.pi)
ls = sig.lombscargle(t, y, f_angular)


print(t[-1])

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(1/f_daily, ls/np.max(ls))
ax.set_xlabel('Period (days)')
plt.show()
# plt.plot(freqs, ps/np.max(ps))\n
