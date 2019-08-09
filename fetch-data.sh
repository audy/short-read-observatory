#!/bin/bash

set -euo pipefail
uri=https://ftp-trace.ncbi.nih.gov/sra/reports/Metadata/NCBI_SRA_Metadata_Full_20190629.tar.gz
wget ${uri}
