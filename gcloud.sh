#!/bin/bash
# Helper to run gcloud with correct Python path
export CLOUDSDK_PYTHON="C:/Users/Admin/AppData/Local/Programs/Python/Python312/python.exe"
"/c/Users/Admin/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud" "$@"
