from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class MetaData:
    dataset_name: str = ""


# Assume 1 metadata file for whole dataset, and metadata is consistent across files
# All files are same filetype
# All files are netcdf4
@dataclass
class DataSet:
    """"""

    files: List[Path] = None
    metadata: MetaData = None

    @property
    def name(self):
        return self.metadata.dataset_name if self.metadata else ""
