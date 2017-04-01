#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import os
import yaml
import json
import sys

OUTPUT_DIR = 'output'

def main():
    yml_cfg = sys.argv[1]
    with open(yml_cfg) as fp:
        config = yaml.safe_load(fp)

    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    cfg_name = os.path.splitext(os.path.basename(yml_cfg))[0]
    with open('%s/%s.json' % (OUTPUT_DIR, cfg_name), 'w') as fp:
        json_str = json.dumps(config, indent=2)
        print(json_str)
        fp.write(json_str)

main()
