# SPDX-License-Identifier: Apache-2.0

import argparse
import check_model
import os
from pathlib import Path
import subprocess
import sys
import test_utils


def main():
  parser = argparse.ArgumentParser(description='Test settings')
  # default all: test by both onnx and onnxruntime
  # if target is specified, only test by the specified one
  parser.add_argument('--target', required=False, default='all', type=str,
                      help='Test the model by which (onnx/onnxruntime)?',
                      choices=['onnx', 'onnxruntime', 'all'])
  args = parser.parse_args()

  cwd_path = Path.cwd()
  # git fetch first for git diff on GitHub Action
  subprocess.run(['git', 'fetch', 'origin', 'main:main'], cwd=cwd_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  # obtain list of added or modified files in this PR
  obtain_diff = subprocess.Popen(['git', 'diff', '--name-only', '--diff-filter=AM', 'origin/main', 'HEAD'],
  cwd=cwd_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdoutput, stderroutput = obtain_diff.communicate()
  diff_list = stdoutput.split()

  # identify list of changed onnx models in model Zoo
  model_list = [str(model).replace("b'","").replace("'", "") for model in diff_list if ".onnx" in str(model)]
  # run lfs install before starting the tests
  test_utils.run_lfs_install()

  print('\n=== Running ONNX Checker on added models ===\n')
  # run checker on each model
  failed_models = []
  tar_ext_name = '.tar.gz'
  for model_path in model_list:
    model_name = model_path.split('/')[-1]
    tar_name = model_name.replace('.onnx', tar_ext_name)
    print(f'==============Testing {model_name}==============')

    try:
        # Step 1: check the onnx model and test_data_set from .tar.gz by ORT
        # replace '.onnx' with '.tar.gz'
      tar_gz_path = f'{model_path[:-5]}.tar.gz'
      print(tar_gz_path)
      test_data_set = []
        # if tar.gz exists, git pull and try to get test data
      if args.target in ['onnxruntime', 'all'] and os.path.exists(tar_gz_path):
        test_utils.pull_lfs_file(tar_gz_path)
        # check whether 'test_data_set_0' exists
        model_path_from_tar, test_data_set = test_utils.extract_test_data(tar_gz_path)
        # finally check the onnx model from .tar.gz by ORT
        # if the test_data_set does not exist, create the test_data_set
        check_model.run_backend_ort(model_path_from_tar, test_data_set)
        print(f'[PASS] {tar_name} is checked by onnxruntime. ')

      # Step 2: check the uploaded onnx model by ONNX
      # git pull the onnx file
      test_utils.pull_lfs_file(model_path)
        # 2. check the uploaded onnx model by ONNX
      if args.target in ['onnx', 'all']:
        check_model.run_onnx_checker(model_path)
        print(f'[PASS] {model_name} is checked by onnx. ')

    except Exception as e:
      print(f'[FAIL] {model_name}: {e}')
      failed_models.append(model_path)
      test_utils.remove_onnxruntime_test_dir()

    # remove the produced tar directory
    test_utils.remove_tar_dir()

  if not failed_models:
    print(f'{len(model_list)} models have been checked. ')
  else:
    print(f'In all {len(model_list)} models, {len(failed_models)} models failed. ')
    sys.exit(1)

if __name__ == '__main__':
    main()
