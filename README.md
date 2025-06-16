# Exergaming Study
16-Jun-2025, David Herzig

## Data Enhacement Script
The enrich_data.py script performs post-processing on gaming session archives by computing and appending additional analytical data.

Each gaming session generates a ZIP archive (e.g., d19d232e1d8c329e7e87b9b3bfa26d46_133304216916983730.zip) containing a JSON file and a corresponding log file. All session archives are expected to reside in a single directory.

To execute the script, run:
'''
python enrich_data.py DATA_FOLDER
'''
Here, DATA_FOLDER refers to the directory containing the session ZIP files. The script will iterate over each ZIP file in the specified directory.

For each archive, if the corresponding enriched data file has already been generated (e.g., from a prior run), it will be skipped. Otherwise, the script will:

Extract the contents of the ZIP file.

Use the extracted files to compute the enriched data.

Write the result to a file named FILENAME_info_v1.json, where FILENAME corresponds to the base name of the original ZIP archive.

After successful generation of the enriched data file, the extracted contents will be deleted, while the original ZIP archive will remain intact.

