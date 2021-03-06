# -*- coding: utf-8 -*-
"""Two-component Widom insertion through RaspaBaseWorkChain"""

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run
from aiida.orm import CifData, Code, Dict, SinglefileData
from aiida_raspa.workchains import RaspaBaseWorkChain


@click.command('cli')
@click.argument('codelabel')
def main(codelabel):
    """Run base workchain"""

    # pylint: disable=no-member

    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    print("Testing RASPA Xenon and Krypton widom insertion through RaspaBaseWorkChain ...")

    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 500,
                "PrintEvery": 200,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "ExternalTemperature": 300.0,
                }
            },
            "Component": {
                "krypton": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                    "BlockPocketsFileName": "block_tcc1rs_methane",
                },
                "xenon": {
                    "MoleculeDefinition": "TraPPE",
                    "WidomProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                    "BlockPocketsFileName": "block_tcc1rs_xenon",
                },
            },
        })

    # framework
    pwd = os.path.dirname(os.path.realpath(__file__))
    structure = CifData(file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'TCC1RS.cif'))
    structure_label = structure.filename[:-4].lower()

    block_pocket_node1 = SinglefileData(
        file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'block_pocket.block')).store()
    block_pocket_node2 = SinglefileData(
        file=os.path.join(pwd, '..', 'simple_calculations', 'files', 'block_pocket.block')).store()

    # Constructing builder
    builder = RaspaBaseWorkChain.get_builder()

    # Specifying the code
    builder.raspa.code = code

    # Specifying the framework
    builder.raspa.framework = {
        structure_label: structure,
    }

    # Specifying the input parameters
    builder.raspa.parameters = parameters

    # Specifying the block pockets
    builder.raspa.block_pocket = {
        "block_tcc1rs_methane": block_pocket_node1,
        "block_tcc1rs_xenon": block_pocket_node2,
    }

    # Add fixtures that could handle physics-related problems.
    builder.fixtures = {
        'fixture_001': ('aiida_raspa.utils', 'check_widom_convergence', 0.1, 2000),
    }

    # Specifying the scheduler options
    builder.raspa.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }

    run(builder)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
