#!/usr/bin/env python
import argparse
import os
import json
import subprocess
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


def extract_existing_wf_ids():
    existing_workflow_ids = {}
    for wf in glob.glob("data/*/*.ga"):
        with open(wf, 'r') as handle:
            data = json.load(handle)
            existing_workflow_ids[data['id']] = data['name']
    return existing_workflow_ids


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

    existing_wf = extract_existing_wf_ids()
    import pprint; pprint.pprint(existing_wf)

    gi = galaxy.GalaxyInstance(args.url, args.key)

    testCases = []
    for wf in gi.workflows.get_workflows():
        if not os.path.exists(wf['owner']):
            os.makedirs(wf['owner'])

        if wf['id'] in existing_wf:
            original_name = existing_wf[wf['id']]
            # TODO: FIX THIS. It tries to overwrite files weirdly.
            # If the name has changed, `git mv`
            # if original_name != wf['name']:
                # print('\t', 'Current', wf['id'], wf['name'], 'Existing', existing_wf[wf['id']])
                # subprocess.check_call([
                    # 'git', 'mv',
                    # os.path.join('data', wf['owner'], original_name + '.ga'),
                    # os.path.join('data', wf['owner'], wf['name'] + '.ga')
                # ])

        with xunit('galaxy', 'download_wf.%s' % wf['id']) as testCase:
            wf_data = gi.workflows.export_workflow_json(wf['id'])
            with open(os.path.join('data', wf['owner'], wf['name'] + '.ga'), 'w') as handle:
                wf_data['id'] = wf['id']
                json.dump(wf_data, handle, sort_keys=True, indent=4)
        testCases.append(testCase)


    with xunit('galaxy', 'git-commit') as gitTestCase:
        subprocess.check_call([
            'git', 'add', 'data'
        ])
        numstat = subprocess.check_output([
            'git', 'diff', '--cached', '--numstat',
        ])
        # Only commit if things were added.
        if len(numstat.strip()) > 0:
            subprocess.check_call([
                'git', 'commit', '-m', 'Automated commit for %s' % datetime.datetime.today()
            ])

    ts = xunit_suite('Workflow Backup', testCases + [gitTestCase])
    args.xunit_output.write(xunit_dump([ts]))

if __name__ == "__main__":
    __main__()
