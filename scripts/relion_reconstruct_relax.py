#!/usr/bin/env python

# **************************************************************************
# *
# * Author:  Juha T. Huiskonen (juha@strubi.ox.ac.uk)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# **************************************************************************

import os
import sys

from pyworkflow.em import runProgram
from pyrelion import MetaData
from localrec import *
import argparse


class ReconstructRelaxSymmetry():
    def define_parser(self):
        self.parser = argparse.ArgumentParser(
            description="Relaxes a symmetric reconstruction.")
        required = self.parser.add_argument_group('required arguments')
        add = self.parser.add_argument  # shortcut
        addr = required.add_argument

        add('input_star', help="Input STAR filename with particles.")
        add('--sym', default="C1", help="Symmetry of the reconsruction.")
        addr('--angpix', type=float, help="Pixel size (A).", required=True)
        addr('--maxres', type=float, help="Maximum resolution (A).", required=True)
        addr('--output', required=True, help="Output STAR filename.")
        addr('--map', required=True, help="Output reconstuction filename.")
        addr('--j', default='1', type=int, required=False, help="Number of threads.")

    def usage(self):
        self.parser.print_help()

    def error(self, *msgs):
        self.usage()
        print "Error: " + '\n'.join(msgs)
        print " "
        sys.exit(2)

    def validate(self, args):
        if len(sys.argv) == 1:
            self.error("Error: No input file given.")

        if not os.path.exists(args.input_star):
            self.error("Error: Input file '%s' not found."
                       % args.input_star)

    def main(self):
        self.define_parser()
        args = self.parser.parse_args()

        self.validate(args)

        print "Calculating symmetry related orientations..."

        md = MetaData(args.input_star)
        mdOut = MetaData()
        mdOut.addLabels(md.getLabels())
        mdOut.addLabels('rlnAngleRotPrior','rlnAngleTiltPrior','rlnAnglePsiPrior')
        mdOut.removeLabels('rlnOriginalParticleName', 'rlnParticleName')

        new_particles = []

        symmetry_matrices = matrix_from_symmetry(args.sym)

        for particle in md:
            angles_to_radians(particle)
            new_particles.extend(create_symmetry_related_particles(particle, symmetry_matrices, True))
        mdOut.addData(new_particles)

        for particle in mdOut:
            particle.rlnAngleRotPrior = particle.rlnAngleRot
            particle.rlnAngleTiltPrior = particle.rlnAngleTilt
            particle.rlnAnglePsiPrior = particle.rlnAnglePsi

        mdOut.write(args.output)

        print "Calculating an asymmetric reconstruction..."
        runProgram('relion_reconstruct', '--i %s --o %s --ctf --sym C1 --angpix %s --maxres %s --j %s'
                             % (args.output, args.map, args.angpix, args.maxres, args.j))


        print " "
        print "All done!"
        print " "

if __name__ == "__main__":

    ReconstructRelaxSymmetry().main()
