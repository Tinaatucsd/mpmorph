from __future__ import division, print_function, unicode_literals, absolute_import

from monty.json import MontyEncoder
import json
from atomate.vasp.database import VaspCalcDb
from atomate.utils.utils import get_logger

logger = get_logger(__name__)


class VaspMDCalcDb(VaspCalcDb):
    """
    Adapted from atomate.vasp.database

    Class to help manage database insertions of Vasp drones
    """

    def __init__(self, host="localhost", port=27017, database="vasp", collection="tasks", user=None,
                 password=None):
        super(VaspMDCalcDb, self).__init__(host, port, database, collection, user, password)

    def insert_task(self, task_doc, parse_dos=False, parse_bs=False, md_structures=False):
        """
        Inserts a task document (e.g., as returned by Drone.assimilate()) into the database.
        Handles putting DOS and band structure into GridFS as needed.
        Args:
            task_doc: (dict) the task document
            parse_dos: (bool) attempt to parse dos in task_doc and insert into Gridfs
            parse_bs: (bool) attempt to parse bandstructure in task_doc and insert into Gridfs
        Returns:
            (int) - task_id of inserted document
        """

        # insert dos into GridFS
        if parse_dos and "calcs_reversed" in task_doc:
            if "dos" in task_doc["calcs_reversed"][0]:  # only store idx=0 DOS
                dos = json.dumps(task_doc["calcs_reversed"][0]["dos"], cls=MontyEncoder)
                gfs_id, compression_type = self.insert_gridfs(dos, "dos_fs")
                task_doc["calcs_reversed"][0]["dos_compression"] = compression_type
                task_doc["calcs_reversed"][0]["dos_fs_id"] = gfs_id
                del task_doc["calcs_reversed"][0]["dos"]

        # insert band structure into GridFS
        if parse_bs and "calcs_reversed" in task_doc:
            if "bandstructure" in task_doc["calcs_reversed"][0]:  # only store idx=0 BS
                bs = json.dumps(task_doc["calcs_reversed"][0]["bandstructure"], cls=MontyEncoder)
                gfs_id, compression_type = self.insert_gridfs(bs, "bandstructure_fs")
                task_doc["calcs_reversed"][0]["bandstructure_compression"] = compression_type
                task_doc["calcs_reversed"][0]["bandstructure_fs_id"] = gfs_id
                del task_doc["calcs_reversed"][0]["bandstructure"]

        # insert structures  at each ionic step into GridFS
        if md_structures and "calcs_reversed" in task_doc:
            structures = json.dumps(task_doc["calcs_reversed"][0]["structures"], cls=MontyEncoder)
            gfs_id, compression_type = self.insert_gridfs(structures, "structures_fs")
            task_doc["calcs_reversed"][0]["structures_compression"] = compression_type
            task_doc["calcs_reversed"][0]["structures_fs_id"] = gfs_id
            del task_doc["output"]["structures"]

        # insert the task document and return task_id
        return self.insert(task_doc)