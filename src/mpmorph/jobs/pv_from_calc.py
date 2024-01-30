from __future__ import annotations
from dataclasses import dataclass
from jobflow import Maker, job, Response
from pymatgen.core.structure import Structure

# from atomate2.vasp.schemas.task import TaskDocument
from atomate2.amset.schemas import AmsetTaskDocument
from atomate2.vasp.jobs.core import MDMaker
from .tasks.m3gnet_input import M3GNetMDInputs
from .tasks.chgnet_input import CHGNetMDInputs
from chgnet.model.dynamics import CHGNetCalculator
from chgnet.model.model import CHGNet
from .tasks.m3gnet_md_task import run_m3gnet
from .tasks.chgnet_md_task import run_chgnet

from ..schemas.m3gnet_md_calc import M3GNetMDCalculation
from ..schemas.chgnet_md_calc import CHGNetMDCalculation

from mpmorph.schemas.pv_data_doc import MDPVDataDoc
import numpy as np


@dataclass
class PVFromCalc(Maker):
    @job
    def make(self, structure, scale_factor=None):
        struct = structure.copy()

        if scale_factor is not None:
            struct.scale_lattice(struct.volume * scale_factor)

        calc_doc = self.run_md(struct)
        pv_doc = self.build_doc(calc_doc)

        return Response(output=pv_doc)


@dataclass
class PVFromM3GNet(PVFromCalc):

    name: str = "PV_FROM_M3GNET"
    parameters: M3GNetMDInputs = None

    def run_md(self, structure: Structure, **kwargs):
        calc_doc = run_m3gnet(structure, self.parameters, self.name, **kwargs)

        return calc_doc

    def build_doc(self, m3gnet_calc: M3GNetMDCalculation):
        v_data = m3gnet_calc_to_vol(m3gnet_calc)
        p_data = m3gnet_calc_to_pressure(m3gnet_calc)
        return MDPVDataDoc(task_label='PV_FROM_M3GNET', volume=v_data, pressure=p_data)

@dataclass
class PVFromCHGNet(PVFromCalc):

    name: str = "PV_FROM_CHGNET"
    parameters: CHGNetMDInputs = None
    model: str | None = None

    def run_md(self, structure: Structure, **kwargs):
        _model = CHGNet.from_file(self.model) if isinstance(self.model,str) else CHGNet()
        calc_doc = run_chgnet(
            structure=structure,
            inputs=self.parameters,
            model=_model,
            name=self.name, **kwargs)

        return calc_doc

    def build_doc(self, chgnet_calc: CHGNetMDCalculation):
        v_data = chgnet_calc_to_vol(chgnet_calc)
        p_data = chgnet_calc_to_pressure(chgnet_calc)
        return MDPVDataDoc(task_label='PV_FROM_CHGNET', volume=v_data, pressure=p_data)

def m3gnet_calc_to_vol(m3gnet_calc: M3GNetMDCalculation):
    volume = m3gnet_calc.trajectory[-1].lattice.volume
    return volume

def chgnet_calc_to_vol(chgnet_calc: CHGNetMDCalculation):
    volume = chgnet_calc.trajectory[-1].lattice.volume
    return volume

def m3gnet_calc_to_pressure(m3gnet_calc: M3GNetMDCalculation):
    # retrieve stresses in Voigt order (i.e. xx, yy, zz, yz, xz, xy)
    stresses = m3gnet_calc.trajectory.frame_properties[-1]["stress"]
    trace = sum(stresses[0:3])
    pressure = 1 / 3 * trace
    return pressure


def chgnet_calc_to_pressure(chgnet_calc: CHGNetMDCalculation):
    # retrieve stresses in Voigt order (i.e. xx, yy, zz, yz, xz, xy)
    stresses = chgnet_calc.trajectory.frame_properties[-1]["stress"]
    trace = sum(stresses[0:3])
    pressure = 1 / 3 * trace
    return pressure
    
@dataclass
class PVFromVasp(PVFromCalc):

    name: str = "PV_FROM_VASP"
    md_maker: Maker = MDMaker()

    def run_md(self, structure: Structure, **kwargs):
        # TODO: Not sure about this - I think .original accesses the
        # undecorated make function definition. To me this is a big
        # code smell - if you have to take the code out of the @job to reuse it,
        # it never should have been in the @job, but this is taken from examples
        # in atomate2 (e.g. TransmuterMaker), so hopefully it will do for now
        return self.md_maker.make.original(self, structure)

    def build_doc(self, task_document: M3GNetMDCalculation): # Hui is confused that the class name is VASP while task_document is M3GNetMDCalculation
        v_data = task_doc_to_volume(task_document)
        p_data = task_doc_to_pressure(task_document)
        return MDPVDataDoc(task_label='PV_FROM_VASP',volume=v_data, pressure=p_data)


def task_doc_to_volume(task_doc: AmsetTaskDocument) -> float:
    volume = task_doc.calcs_reversed[-1].output.ionic_steps[-1].structure.lattice.volume
    return volume


def task_doc_to_pressure(task_doc: AmsetTaskDocument) -> float:  # TODO
    stress_tensor = task_doc.calcs_reversed[-1].output.ionic_steps[-1].stress
    pressure = 1 / 3 * np.trace(stress_tensor)
    return pressure
