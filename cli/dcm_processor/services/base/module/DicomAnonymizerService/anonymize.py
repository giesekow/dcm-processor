import os
import subprocess
import shlex
import pydicom
from .utils import read_csv_table, write_temp_table, append_hash_table, delete_temp_table, get_correspondence
import sys

MODULES = os.getenv('MODULES')
DATA = os.getenv('DATA')

CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config')

hash_table = os.path.join(CONFIG, 'hash_table.csv')
anony_script = os.path.join(CONFIG, 'dicom-anonymizer.script')
pseudonyms_table = os.path.join(CONFIG, 'psudonyms.csv')

temp_table = os.path.join(DATA, 'temp_table.properties')
anonymizer = os.path.join(os.path.dirname(os.path.realpath(__file__)),'DAT.jar')

def anonymize(path):
    series = []
    for r, _, f in os.walk(path):
        for file in f:
            series.append(os.path.join(r,file))

    ptid = pydicom.dcmread(series[0]).PatientID
    
    if os.path.isfile(pseudonyms_table):
        pseudonyms_dict = read_csv_table(pseudonyms_table)
        
    else:
        pseudonyms_dict = {}

    pseudonym, hashed = get_correspondence(ptid, pseudonyms_dict,hash_table)
    if hashed:
        append_hash_table(hash_table,ptid,pseudonym)

    write_temp_table(ptid,pseudonym,temp_table)
    
    anonymized_path = f"{path}_anon"

    an_path = os.path.join(anonymized_path)
    if not os.path.isdir(an_path):
        os.makedirs(an_path)
    
    command = "java -jar " + anonymizer +" -in " +'"' + path + '"' +" -out " + '"' + anonymized_path + '"'  + " -da " + '"' +anony_script + '"' + " -lut " + '"' +temp_table + '"' +" -v"

    os.system(command)
    os.system(f"rm -rf {path} && mv {anonymized_path} {path}")

    delete_temp_table(temp_table) 

