import os
import hashlib
import csv
import sys
from .fhir_lib import get_fhir_pseudonym

def read_csv_table(table_path):
    with open(table_path) as f:
        reader = csv.reader(f)
        pseudonyms_dict = {str(rows[0]):str(rows[1]) for rows in reader}
        f.close()
    return pseudonyms_dict


def write_temp_table(ptid,pseudonym,temp_pse):
    to_write_line = 'ptid/{}={}\n'.format(ptid,pseudonym)
    with open(temp_pse, "w") as f:
        f.write(to_write_line)
        f.close()

def append_hash_table(table_path,ptid,pseudonym):
    with open(table_path, 'a+') as f:
        fieldnames = ['PatientID', 'Pseudonym']
    
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if os.path.getsize(table_path) ==0:
            writer.writeheader()
            
        writer.writerow({'PatientID': ptid,'Pseudonym':pseudonym})
        f.close()
def delete_temp_table(temp_pse):
    os.remove(temp_pse)

def get_correspondence(ptid,pseudonyms_dict,hash_table, params=None):
    print('getting correspondence', file=sys.stdout)

    if str(ptid) in pseudonyms_dict.keys():
        print('in pseudonyms table', file=sys.stdout)
        return pseudonyms_dict[ptid], False

    pseudonyms = get_fhir_pseudonym(ptid=ptid, params=params)
    if not pseudonyms is None:
        print('from fhir service', file=sys.stdout)
        return pseudonyms, True

    if os.path.isfile(hash_table):
        print('checking hashtable', file=sys.stdout)
        hash_dict = read_csv_table(hash_table)
        if str(ptid) in hash_dict.keys():
            return hash_dict[ptid], False
        else: 
            return hashlib.md5(str(ptid+'Y7t5').encode('utf-8')).hexdigest(), True
    else:
        return hashlib.md5(str(ptid+'Y7t5').encode('utf-8')).hexdigest(), True
