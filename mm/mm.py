import os.path
import sys
import argparse
import traceback
import json
import lib.config as config
import lib.mm_util as util
import time #TODO: remove
import urllib
from suds.client import Client
from lib.mm_connection import MavensMatePluginConnection
from lib.mm_client import MavensMateClient

request_payload = util.get_request_payload()
#config.logger.debug('\n\n\n>>>>>>>>\nhandling request with payload >>>>>')
#config.logger.debug(request_payload)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation') #name of the operation being requested
    parser.add_argument('-c', '--client') #name of the plugin client ("Sublime Text", "TextMate", "Notepad++", "BBEdit", etc.)
    parser.add_argument('-p', '--projectname') #name of the project
    parser.add_argument('-d', '--projectdirectory') #name of the project
    parser.add_argument('--callback') #some terminal script to run upon completion of a command
    parser.add_argument('--ui', action='store_true', default=False, 
        dest='ui_switch', help='Include flag to launch the default UI for the operation')
    parser.add_argument('--html', action='store_true', default=False, 
        dest='respond_with_html', help='Include flag if you want the response in HTML')
    args = parser.parse_args()
    operation = args.operation
    setup_connection(args)

    #if the arg switch argument is included, the request is to launch the out of box
    #MavensMate UI, so we generate the HTML for the UI and launch the process
    #example: mm -o new_project --ui
    if args.ui_switch == True:
        #os.system('killAll MavensMateWindowServer') #TODO: try/except?
        tmp_html_file = util.generate_ui(operation)
        util.launch_ui(tmp_html_file)
        print util.generate_success_response('OK')
    else:        
        if operation == 'new_project':
            new_project()
        if operation == 'edit_project':
            edit_project()    
        elif operation == 'checkout_project':
            checkout_project()
        elif operation == 'compile_project':
            compile_project()
        elif operation == 'new_metadata':
            new_metadata()
        elif operation == 'clean_project':
            clean_project()
        elif operation == 'refresh':
            refresh()
        elif operation == 'compile':
            compile_selected_metadata()
        elif operation == 'delete':
            delete_selected_metadata()
        elif operation == 'get_active_session':
            get_active_session()
        elif operation == 'update_credentials':
            update_credentials()
        elif operation == 'execute_apex':
            execute_apex()
        elif operation == 'deploy_to_server' or operation == 'deploy':
            deploy_to_server(args)
        elif operation == 'unit_test' or operation == 'test':
            run_unit_tests(args)
        elif operation == 'list_metadata':
            list_metadata()
        elif operation == 'index_metadata':
            index_metadata(args)    
        elif operation == 'list_connections':
            list_connections()
        elif operation == 'new_connection':
            new_connection()
        elif operation == 'delete_connection':
            delete_connection()

    if args.callback != None:
        os.system(args.callback)

# each operation sets up a single connection
# the connection holds information about the plugin running it
# and establishes a project object
def setup_connection(args):
    if 'project_name' in request_payload or 'project_directory' in request_payload:
        project_name        = request_payload.get('project_name', args.projectname)
        project_directory   = request_payload.get('project_directory', args.projectdirectory)
        config.connection = MavensMatePluginConnection(
            client=args.client or 'Sublime Text', 
            project_directory=project_directory,
            project_name=project_name,
            ui=args.ui_switch
        )
    else:
        config.connection = MavensMatePluginConnection(client=args.client or 'Sublime Text')

# echo '{ "username" : "joeferraro4@force.com", "password" : "352198", "metadata_type" : "ApexClass" ' | joey2 mavensmate.py -o 'list_metadata'
def list_metadata():
    client = MavensMateClient(credentials={
        "sid"                   : request_payload.get('sid', None),
        "metadata_server_url"   : urllib.unquote(request_payload.get('murl', None))
    }) 
    print json.dumps(client.list_metadata(request_payload['metadata_type']))

def list_connections():
    print config.connection.project.get_org_connections()

def new_connection():
    print config.connection.project.new_org_connection(request_payload)

def delete_connection():
    print config.connection.project.delete_org_connection(request_payload)

def compile_selected_metadata():
    print config.connection.project.compile_selected_metadata(request_payload)

def delete_selected_metadata():
    print config.connection.project.delete_selected_metadata(request_payload)

def index_metadata(args):
    index_result = config.connection.project.index_metadata()
    if args.respond_with_html ==  True:
        html = util.generate_html_response(args.operation, index_result, request_payload)
        print util.generate_success_response(html, "html")
    else:
        print index_result

def new_project():
    print config.connection.new_project(request_payload,action='new')

def edit_project():
    print config.connection.project.edit(request_payload)

def checkout_project():
    print config.connection.new_project(request_payload,action='checkout')

def compile_project():
    print config.connection.project.compile()

def clean_project():
    print config.connection.project.clean()

def refresh():
    print config.connection.project.refresh_selected_metadata(request_payload)

def new_metadata():
    print config.connection.project.new_metadata(request_payload)

def execute_apex():
    print config.connection.project.execute_apex(request_payload)

# echo '{ "project_name" : "bloat", "classes" : [ "MyTester" ] }' | joey2 mavensmate.py -o 'test'
def run_unit_tests(args):
    test_result = config.connection.project.run_unit_tests(request_payload)
    if args.respond_with_html ==  True:
        html = util.generate_html_response(args.operation, test_result, request_payload)
        print util.generate_success_response(html, "html")
    else:
        print test_result

def deploy_to_server(args):
    deploy_result = config.connection.project.deploy_to_server(request_payload)
    if args.respond_with_html == True:
        html = util.generate_html_response(args.operation, deploy_result, request_payload)
        print util.generate_success_response(html, "html")
    else:
        print deploy_result

# echo '{ "username" : "mm@force.com", "password" : "force", "org_type" : "developer" }' | joey2 mavensmate.py -o 'get_active_session'
def get_active_session():
    try:
        client = MavensMateClient(credentials={
            "username" : request_payload['username'],
            "password" : request_payload['password'],
            "org_type" : request_payload['org_type']
        }) 
        
        response = {
            "sid"                   : client.sid,
            "user_id"               : client.user_id,
            "metadata_server_url"   : client.metadata_server_url,
            "metadata"              : client.get_org_metadata(),
            "success"               : True
        }
        print util.generate_response(response)
    except BaseException, e:
        print util.generate_error_response(e.message)

def update_credentials():
    try:
        config.connection.project.username = request_payload['username']
        config.connection.project.password = request_payload['password']
        config.connection.project.org_type = request_payload['org_type']
        config.connection.project.update_credentials()
        print util.generate_success_response('Success')
    except BaseException, e:
        #print traceback.print_exc()
        print util.generate_error_response(e.message)

if  __name__ == '__main__':
    main()