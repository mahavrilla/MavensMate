#when mavensmate binary is executed, a plugin connection should be created immediately
#plugin connection should have a single instance of a mm_client associated

import os
import json
import mm_util
import sys
from enum import enum
from mm_project import MavensMateProject

class MavensMatePluginConnection(object):

    PluginClients = enum(SUBLIME_TEXT='Sublime Text', NOTEPAD_PLUS_PLUS='Notepad++', TEXTMATE='TextMate')

    def __init__(self, **kwargs):
        self.platform               = sys.platform
        self.plugin_client          = kwargs.get('client', 'Sublime Text') #=> "Sublime Text", "Notepad++", "TextMate"
        self.plugin_client_version  = kwargs.get('client_version', '2.0.1') #=> "1.0", "1.1.1", "v1"
        self.plugin_client_settings = self.get_plugin_client_settings()
        self.workspace              = self.get_workspace()
        self.project_directory      = kwargs.get('project_directory', None)
        self.project_name           = kwargs.get('project_name', None)
        self.project                = None
        self.sfdc_api_version       = self.get_sfdc_api_version()
        self.ui                     = kwargs.get('ui', False) #=> whether this connection was created for the purposes of generating a UI
        #TODO: i think 27/28 is bad logic
        if mm_util.SFDC_API_VERSION == "":
            mm_util.SFDC_API_VERSION = self.sfdc_api_version
        if self.project_directory != None and os.path.exists(self.project_directory):
            self.project = MavensMateProject(location=self.project_directory,ui=self.ui)
        elif self.project_name != None and self.project_name != '' and os.path.exists(self.workspace+"/"+self.project_name):
            self.project = MavensMateProject(location=self.workspace+"/"+self.project_name,project_name=self.project_name,ui=self.ui)

    #returns the workspace for the current connection (/Users/username/Workspaces/MavensMate)
    def get_workspace(self):
        return self.plugin_client_settings['user']['mm_workspace']

    #returns the MavensMate settings as a dict for the current plugin
    def get_plugin_client_settings(self):
        if self.plugin_client == self.PluginClients.SUBLIME_TEXT:
            if self.platform == 'darwin':
                default_settings = mm_util.parse_json_from_file(os.path.expanduser('~/Library/Application Support/Sublime Text 2/Packages/MavensMate/mavensmate.sublime-settings'))
                user_settings    = mm_util.parse_json_from_file(os.path.expanduser('~/Library/Application Support/Sublime Text 2/Packages/User/mavensmate.sublime-settings'))
                return {
                    'user'    : user_settings,
                    'default' : default_settings
                }
            elif self.platform == 'win32' or self.platform == 'cygwin':
                default_settings = mm_util.parse_json_from_file(path.join(environ['APPDATA'], 'Sublime Text 2', 'Packages', 'MavensMate')+"mavensmate.sublime-settings")
                user_settings = mm_util.parse_json_from_file(path.join(environ['APPDATA'], 'Sublime Text 2', 'Packages', 'User')+"mavensmate.sublime-settings")
                return {
                    'user'    : user_settings,
                    'default' : default_settings
                }
            elif self.platform == 'linux2':
                pass
        else:
            return None

    #retrieves metadata from server, creates local project
    def new_project(self, params, **kwargs):
        try:
            if 'username' not in params or params['username'] == '':
                return mm_util.generate_error_response('Please specify a username')
            if 'password' not in params or params['password'] == '':
                return mm_util.generate_error_response('Please specify a password')
            if 'project_name' not in params or params['project_name'] == '':
                return mm_util.generate_error_response('Please specify a project name')

            if 'package' not in params or params['package'] == []:
                params['package'] = {
                    'ApexClass'         : '*',
                    'ApexComponent'     : '*',
                    'ApexPage'          : '*',
                    'ApexTrigger'       : '*',
                    'StaticResource'    : '*'
                }
            self.project = MavensMateProject(params)
            if ('action' in kwargs and kwargs['action'] == 'new') or 'action' not in kwargs:
                result = self.project.retrieve_and_write_to_disk()
            elif 'action' in kwargs and kwargs['action'] == 'checkout':
                result = self.project.checkout_from_source_control()

            if json.loads(result)['success'] == True:
                #opens project based on the client
                if self.plugin_client == self.PluginClients.SUBLIME_TEXT:
                    if self.platform == 'darwin':
                        os.system("'/Applications/Sublime Text 2.app/Contents/SharedSupport/bin/subl' --project '{0}'".format(self.project.location+"/"+self.project.project_name+".sublime-project"))

            return result
        except BaseException, e:
            return mm_util.generate_error_response(e.message)

    def get_sfdc_api_version(self):
        if self.plugin_client_settings == None:
            return '26.0'
        else:
            return self.get_plugin_client_setting('mm_api_version')
            # if 'mm_api_version' in self.plugin_client_settings['user'] and self.plugin_client_settings['user']['mm_api_version'] != None:
            #     return self.plugin_client_settings['user']['mm_api_version']
            # else:
            #     return self.plugin_client_settings['default']['mm_api_version']

    def get_plugin_client_setting(self, setting_name):
        if setting_name in self.plugin_client_settings['user'] and self.plugin_client_settings['user'][setting_name] != None:
            return self.plugin_client_settings['user'][setting_name]
        else:
            return self.plugin_client_settings['default'][setting_name]

    # tooling_api_extensions = ['.cls', '.trigger', '.page', '.component']

    # def alert(message):
    #     return { "success" : False, "body" : message }




