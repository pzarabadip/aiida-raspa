#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Restart from simple RASPA calculation."""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import click

from aiida.common import NotExistent
from aiida.engine import run_get_pk, run
from aiida.orm import Code, Dict, load_node
from aiida.plugins import DataFactory

# data objects
CifData = DataFactory('cif')  # pylint: disable=invalid-name


@click.command('cli')
@click.argument('codelabel')
@click.option('--previous_calc', '-p', required=True, type=int, help='PK of test_raspa_base.py calculation')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def main(codelabel, previous_calc, submit):
    """Prepare and submit restart from simple RASPA calculation."""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    # parameters
    parameters = Dict(
        dict={
            "GeneralSettings": {
                "SimulationType": "MonteCarlo",
                "NumberOfCycles": 2000,
                "NumberOfInitializationCycles": 2000,
                "PrintEvery": 1000,
                "Forcefield": "GenericMOFs",
                "EwaldPrecision": 1e-6,
                "CutOff": 12.0,
                "HeliumVoidFraction": 0.149,
            },
            "System": {
                "tcc1rs": {
                    "type": "Framework",
                    "UnitCells": "1 1 1",
                    "ExternalTemperature": 350.0,
                    "ExternalPressure": 6e5,
                },
            },
            "Component": {
                "methane": {
                    "MoleculeDefinition": "TraPPE",
                    "TranslationProbability": 0.5,
                    "ReinsertionProbability": 0.5,
                    "SwapProbability": 1.0,
                    "CreateNumberOfMolecules": 0,
                }
            },
        })

    # framework
    framework = CifData(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files', 'TCC1RS.cif'))

    # restart file
    retrieved_parent_folder = load_node(previous_calc).outputs.retrieved

    # Contructing builder
    builder = code.get_builder()
    builder.framework = {
        "tcc1rs": framework,
    }
    builder.parameters = parameters
    builder.retrieved_parent_folder = retrieved_parent_folder
    builder.metadata.options = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        },
        "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
        "withmpi": False,
    }
    builder.metadata.dry_run = False
    builder.metadata.store_provenance = True

    if submit:
        print("Testing RASPA with simple input, restart ...")
        res, pk = run_get_pk(builder)
        print("calculation pk: ", pk)
        print("Total Energy average (tcc1rs):", res['output_parameters'].dict.tcc1rs['general']['total_energy_average'])
        print("OK, calculation has completed successfully")
    else:
        print("Generating test input ...")
        builder.metadata.dry_run = True
        builder.metadata.store_provenance = False
        run(builder)
        print("Submission test successful")
        print("In order to actually submit, add '--submit'")
    print("-----")


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter

# EOF
