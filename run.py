#!/usr/bin/env python
import argparse
import os
import json
import subprocess
import time
from tqdm import tqdm
import glob
import logging
import datetime
from bioblend import galaxy
from xunit_wrapper import xunit, xunit_suite, xunit_dump


logging.basicConfig(format='[%(asctime)s][%(lineno)d][%(module)s] %(message)s', level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("bioblend").setLevel(logging.WARNING)
NOW = datetime.datetime.now()
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BUILD_ID = os.environ.get('BUILD_NUMBER', 'Manual')

def __main__():
    parser = argparse.ArgumentParser(description="""Script to run all workflows mentioned in workflows_to_test.
    It will import the shared workflows are create histories for each workflow run, prefixed with ``TEST_RUN_<date>:``
    Make sure the yaml has file names identical to those in the data library.""")

    parser.add_argument('-k', '--api-key', '--key', dest='key', metavar='your_api_key',
                        help='The account linked to this key needs to have admin right to upload by server path',
                        required=True)
    parser.add_argument('-u', '--url', dest='url', metavar="http://galaxy_url:port",
                        help="Be sure to specify the port on which galaxy is running",
                        default="http://usegalaxy.org")
    parser.add_argument('-x', '--xunit-output', dest="xunit_output", type=argparse.FileType('w'), default='report.xml',
                        help="""Location to store xunit report in""")
    args = parser.parse_args()

    existing_workflows = glob.glob("data/*/*.ga")
    print(existing_workflows)

    gi = galaxy.GalaxyInstance(args.url, args.key)
    for wf in tqdm(gi.workflows.get_workflows()):
        # {'owner': 'eric-rasche', 'deleted': False, 'id': '1247ee583226c37f', 'url': '/galaxy/api/workflows/1247ee583226c37f', 'published': True, 'name': 'Indel Calling', 'model_class': 'StoredWorkflow', 'latest_workflow_uuid': 'ef482b6d-3497-411f-b3b0-0fe757d391cb'}
        if not os.path.exists(wf['owner']):
            os.makedirs(wf['owner'])

        with open(os.path.join('data', wf['owner'], wf['name'] + '.ga'), 'w') as handle:
            try:
                json.dump(
                    gi.workflows.export_workflow_json(wf['id']),
                    handle,
                    sort_keys=True,
                    indent=4
                )
            except:
                pass

    subprocess.check_call([
        'git', 'add', 'data'
    ])


if __name__ == "__main__":
    __main__()
