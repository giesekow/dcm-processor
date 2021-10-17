"""
Registers two images (pre -> post), performs histogram matching and saves the subtraction (post - pre)

Expects data (two niftis) in ./data
    ./data/pre.nii.gz
    ./data/post.nii.gz

Saves sub.nii.gz to ./data
"""

import os
import sys
import shlex
import subprocess
import nibabel as nib
import numpy as np
from skimage.exposure import match_histograms
import pydicom
import shutil

data = os.path.join(os.getenv("DATA"), 'ms-sub')

def get_niftis(path):
  files = []
  for r,d,f in os.walk(path):
    for fi in f:
      if fi.endswith('.nii.gz'):
        files.append(os.path.join(r,fi))
  return files

def get_dicoms(path):
  files = []
  for r,d,f in os.walk(path):
    for fi in f:
      files.append(os.path.join(r,fi))
  return files

def subtract(dcmpath, niftipath):
  series = get_dicoms(dcmpath)

  if len(series) > 0:

    ds = pydicom.dcmread(series[0])
    ptid = ds.PatientID
    studydate = ds.StudyDate

    patient_folder = os.path.join(data,ptid)
    study_folder = os.path.join(patient_folder,studydate)
    new_nii_path = os.path.join(study_folder,('mssub_'+ptid + '_' + studydate + '.nii.gz'))
    if not os.path.isdir(patient_folder):
      os.makedirs(study_folder)
      shutil.copyfile(niftipath, new_nii_path)
    else:
      os.makedirs(study_folder)
      shutil.copyfile(niftipath, new_nii_path)
      niftis = get_niftis(patient_folder)
      if len(niftis) == 2:
        date1 = int(niftis[0].split('_')[2][:-7])
        date2 = int(niftis[1].split('_')[2][:-7])
        if date1 > date2:
          pre = niftis[1]
          post = niftis[0]
        else:
          pre = niftis[0]
          post = niftis[1]
        process(pre, post, patient_folder)

        shutil.rmtree(os.path.dirname(pre))
        shutil.rmtree(os.path.dirname(post))
                
def process(pre_path, post_path, patient_folder, sub_file=None):   
  pre_reg_file = os.path.join(patient_folder,'pre_reg.nii.gz')
  post_new = os.path.join(patient_folder,'post.nii.gz')
  
  if sub_file is None:
    sub_file = os.path.join(patient_folder,'sub.nii.gz')

  aladin_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"niftyreg/bin/reg_aladin") 

  reg_call = aladin_path + " -rigOnly -ref " + post_path + " -flo " + pre_path + " -res " + pre_reg_file + " -pad 0"
  subprocess.run(shlex.split(reg_call),stdout=subprocess.PIPE,shell=False)

  pre_nib = nib.load(pre_reg_file)
  post_nib = nib.load(post_path)

  pre = pre_nib.get_fdata()
  post = post_nib.get_fdata()

  pre_histmatch = match_histograms(pre,post)

  sub = post - pre_histmatch

  nib.save(nib.Nifti1Image(sub,pre_nib.affine,pre_nib.header),sub_file)

  shutil.copyfile(post_path, post_new)
