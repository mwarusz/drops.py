#!/usr/bin/python2

# note: before "make install" it uses local one (that's why the directory is named drops_py),
#       afterwards - the system one is used (the one installed by "make install"
import sys
sys.path.insert(0, "/home/mwarusz/repos//libcloudphxx/build/bindings/python/")

from drops_py import rhs_lgrngn, parcel, output, distros
from drops_py.defaults import defaults
from drops_py.defaults_Ghan_et_al_1998 import defaults_Ghan_et_al_1998
from drops_py.defaults_Kreidenweis_et_al_2003 import defaults_Kreidenweis_et_al_2003

from argparse import ArgumentParser
import libcloudphxx.common as libcom 
import libcloudphxx as libcl
import numpy as np

print "drops.py A"

# just a few constants not repeat them below
desc = 'drops.py - a parcel model based on libcloudph++'
chcs = ['Ghan_et_al_1998', 'Kreidenweis_et_al_2003']
dhlp = 'default parameter set'

# defining command-line options parser - first without help
# so that it would not be empty when calling parse_known_args() below
prsr = ArgumentParser(add_help=False, description=desc)
prsr.add_argument('--defaults', choices=chcs, help=dhlp)

# first parsing the "defaults" only - to know the defaults
args = prsr.parse_known_args() # TODO: take care of prefix mathing rules = "def" will also match here :(
defclass = 'defaults'
if args[0].defaults is not None:
  defclass = "defaults_" + args[0].defaults
ctor = globals()[defclass]
dflts = ctor()

# redefining prsr, this time with help
prsr = ArgumentParser(add_help=True, description=desc)
prsr.add_argument('--defaults', choices=chcs, help=dhlp)

# one subparser per one microphysics scheme
sprsr = prsr.add_subparsers()

## common options
prsr.add_argument('--outdir',                required=True,                                 help='output directory')
prsr.add_argument('--outfreq',   type=int,   required=True,                                 help='output frequency (every outfreq timesteps)')

prsr.add_argument('--T',         type=float, required=(dflts.T  is None), default=dflts.T,  help='initial temperature [K]')
prsr.add_argument('--p',         type=float, required=(dflts.p  is None), default=dflts.p,  help='initial pressure [Pa]')
prsr.add_argument('--RH',        type=float, required=(dflts.RH is None), default=dflts.RH, help='initial relative humidity [1]')
prsr.add_argument('--w',         type=float, required=(dflts.w  is None), default=dflts.w,  help='vertical velocity [m/s]')

prsr.add_argument('--dt',        type=float, required=(dflts.dt is None), default=dflts.dt, help='timestep [s]')
prsr.add_argument('--nt',        type=int,   required=(dflts.nt is None), default=dflts.nt, help='number of timesteps')

## lgrngn options
prsr_lgr = sprsr.add_parser('lgrngn')
prsr_lgr.add_argument('--sd_conc',   type=int, required=(dflts.sd_conc is None), default=dflts.sd_conc, help='number of super droplets')
prsr_lgr.add_argument('--kappa',     type=float, required=(dflts.kappa   is None), default=dflts.kappa,   help='aerosol hygroscopicity parameter [1]')
prsr_lgr.add_argument('--n_tot',     type=float, required=(dflts.n_tot   is None), default=dflts.n_tot,   help='aerosol concentration @STP [m-3]',         nargs='+')
prsr_lgr.add_argument('--meanr',     type=float, required=(dflts.meanr   is None), default=dflts.meanr,   help='aerosol mean dry radius [m]',              nargs='+')
prsr_lgr.add_argument('--gstdv',     type=float, required=(dflts.gstdv   is None), default=dflts.gstdv,   help='aerosol geometric standard deviation [1]', nargs='+')
prsr_lgr.add_argument('--cloud_r_min', type=float, required=(dflts.cloud_r_min is None), default=dflts.cloud_r_min, help='minimum radius of cloud droplet range [m]')
prsr_lgr.add_argument('--cloud_r_max', type=float, required=(dflts.cloud_r_max is None), default=dflts.cloud_r_max, help='maximum radius of cloud droplet range [m]')
prsr_lgr.add_argument('--cloud_n_bin', type=int, required=(dflts.cloud_n_bin is None), default=dflts.cloud_n_bin, help='number of bins in the cloud droplet range [1]')
prsr_lgr.add_argument('--chem_SO2',  type=float, default=dflts.chem_SO2,  help='SO2 volume concentration [1]')
prsr_lgr.add_argument('--chem_O3',   type=float, default=dflts.chem_O3,   help='O3 volume concentration [1]')
prsr_lgr.add_argument('--chem_H2O2', type=float, default=dflts.chem_H2O2, help='H2O2 volume concentration [1]')

## blk_2m options
prsr_b2m = sprsr.add_parser('blk_2m')
#TODO...

args = prsr.parse_args()

print "drops.py B"

# computing state variables
p_v = np.array([args.RH * libcom.p_vs(args.T)])
p_d = args.p - p_v
r_v = libcom.eps * p_v / p_d
th_d = args.T * pow(libcom.p_1000 / p_d, libcom.R_d / libcom.c_pd)


chem_gas = None
if args.chem_SO2 + args.chem_O3 + args.chem_H2O2 > 0:
  chem_gas = {
    libcl.lgrngn.chem_species_t.SO2  : args.chem_SO2,
    libcl.lgrngn.chem_species_t.O3   : args.chem_O3,
    libcl.lgrngn.chem_species_t.H2O2 : args.chem_H2O2
  }

print "drops.py C"
# performing the simulation
rhs = rhs_lgrngn.rhs_lgrngn(
  args.dt, 
  args.sd_conc, 
  { 
    args.kappa : distros.lognormal(args.n_tot, args.meanr, args.gstdv)
  },
  chem_gas = chem_gas
)
print "drops.py D"
out = output.output_lgr(
  args.outdir, 
  args.dt * np.arange(0, args.nt+1, args.outfreq), # nt+1 to include nt in the time_out, 
  cloud_rng = (args.cloud_r_min, args.cloud_r_max),
  cloud_nbins = args.cloud_n_bin,
  chem_sp = []
) 
print "drops.py E"
stats = {}
parcel.parcel(p_d, th_d, r_v, args.w, args.nt, args.outfreq, out, rhs, stats=stats)

print "drops.py F"
# outputting a setup.gpi file
out = open(args.outdir + '/setup.gpi', mode='w')
for key, val in vars(args).iteritems():
  if isinstance(val, (int, float)):
    out.write(u"%s = %e\n" % (key, val))
  else:
    out.write(u"#%s = %s\n" % (key, val))  

# outputting a stats.gpi file
out = open(args.outdir + '/stats.gpi', mode='w')
for key, val in stats.iteritems():
  out.write(u"%s = %g\n" % (key, float(val)))

