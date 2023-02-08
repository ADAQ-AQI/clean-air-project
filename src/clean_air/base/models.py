from dataclasses import dataclass
from pathlib import Path
from typing import List

from edr_server.core.models import extents, time, metadata

# Aliases to maintain compatibility in the code, normally would just remove and update the references,
# but we know the dependency on edr_server is only to save time in the short-term, and we anticipate it changing again
# in the future, so it's better to do this.
Duration = time.Duration
DateTimeInterval = time.DateTimeInterval
TemporalExtent = extents.TemporalExtent
Metadata = metadata.CollectionMetadata


# Assume 1 metadata file for whole dataset, and metadata is consistent across files
# All files are same filetype
# All files are netcdf4
@dataclass
class DataSet:
    """"""

    files: List[Path] = None
    metadata: Metadata = None

    @property
    def name(self):
        return self.metadata.title if self.metadata else ""

    @property
    def id(self):
        return self.metadata.id if self.metadata else None
