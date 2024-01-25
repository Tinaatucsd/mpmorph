from typing import Optional
from typing import Literal

from dataclasses import dataclass

from ase import units


def one_atmosphere():
    return 1.01325 * units.bar


@dataclass
class CHGNetMDInputs:

    ensemble: str = "nvt"
    temperature: float = 2000.0
    starting_temperature: float = 10.0
    pressure: float = 1.01325e-4,
    timestep: float = 2.0
    taut: Optional[float] = None
    taup: Optional[float] = None
    bulk_modulus:float | None = None
    compressibility_au: Optional[float] = None
    trajectory_fn: str = "out.traj"
    logfile_fn: str = "out.log"
    loginterval: int = 1
    crystal_feas_logfile: str | None = None
    append_trajectory: bool = False
    steps: int = 2000
    on_isolated_atoms: Literal["ignore", "warn", "error"] = "warn"
    save_files: bool = True    
    use_device: str =  'cpu' # use 'cuda' for faster MD


