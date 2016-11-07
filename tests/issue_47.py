#!/usr/bin/env python


import tempfile, subprocess, sys

outdir = tempfile.mkdtemp()
srcdir = sys.argv[1]

cmd = srcdir + "/drops.py --outdir " + outdir +\
" --T 300 --p 100000 --RH .99 --w 1 --dt 1 --nt 2000 --outfreq 10"\
" lgrngn --sd_conc 64 --kappa .8 --n_tot 500e6 --meanr .05e-6 --gstdv 2"

subprocess.check_call(cmd, shell=True)
