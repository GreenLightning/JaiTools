import sublime
import sublime_plugin
import re
import os
import fnmatch
import time

class JaiCompletions(sublime_plugin.EventListener):
  raw_completions = []
  proc_pattern = re.compile(r'\b[a-zA-Z_]\w*\s*:\s*[:=]\s*\([\w\W]*?\)\s*(?:->\s*.*?\s*)?{')
  
  def get_all_jai_content(self, window):
    jai_content = {}
    
    # Load all open jai files from views in case they are dirty
    for view in window.views():
      file_path = view.file_name()
      
      if file_path != None and file_path[-4:] == '.jai':
        entire_buffer = view.find('[\w\W]*', 0)
        
        if entire_buffer == None:
          continue
        
        jai_content[file_path] = view.substr(entire_buffer)
    
    # Load all jai files in the open folders that aren't already in jai_content
    # TODO: Rewrite this with recursive glob if ST3 upgrades Python to 3.5+
    for folder in window.folders():
      for root, dirs, files in os.walk(folder):
        for file in fnmatch.filter(files, '*.jai'):
          file_path = os.path.join(root, file)
            
          if not file_path in jai_content:
            with open(file_path, 'r') as f:
              jai_content[file_path] = f.read()
    
    return jai_content
  
  def get_procs(self, string):
    procs = self.proc_pattern.findall(string)
    return procs
  
  def is_jai_view(self, view):
    file_name = view.file_name()
    if file_name != None and file_name[-4:].lower() == '.jai':
      return True
    elif view.settings().get('syntax').lower().find('Jai') >= 0:
      return True
    else:
      return False
      
  def gather_raw_completions(self, view):
    func_def_pattern = '(?:\s|^)(\w+)\s*::\s*\(([^()"]*)\)\s*(?:->\s*([^{]+))?{'
    formatter = '$1§$2'
    
    new_raw_completions = []
    view.find_all(func_def_pattern, 0, '$1§$2§$3', new_raw_completions)
    
    file_name = view.file_name()
    if file_name != None:
      for completion in new_raw_completions:
        self.raw_completions.append({'def': completion, 'file_name': file_name})
    else:
      for completion in new_raw_completions:
        self.raw_completions.append({'def': completion})
  
  def build_output_params(self, raw_params):
    if raw_params == '':
      return ''
    
    output_params = ''
    
    splitted_params = raw_params.split(',')
    
    for i in range(len(splitted_params)):
      output_params += '${' + str(i+1) + ':'
      output_params += splitted_params[i].strip()
      output_params += '}'
      if i < len(splitted_params) - 1:
        output_params += ', '
    
    return output_params
  
  def build_completion_from_raw(self, raw):
    splitted_completion = raw['def'].split('§')
    name = splitted_completion[0]
    params = splitted_completion[1]
    return_type = splitted_completion[2]
    
    trigger = name + '(' + params + ')'
    
    if return_type != '':
      trigger += ' -> ' + return_type.strip()
      
    if 'file_name' in raw:
      trigger += ' \t' + os.path.basename(raw['file_name'])
    
    replacement = name + '(' + self.build_output_params(params) + ')'
    
    return [trigger, replacement]
    
  def on_query_completions(self, view, prefix, locations):
    start_time = time.time()
    
    if not self.is_jai_view(view):
      return None
    
    # Testing Code
    # path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'TestFolder/TestFile.jai')
    # with open(path, 'r') as f:
      # file = f.read()
    # self.get_procs(file)
      
    self.raw_completions = []
    self.gather_raw_completions(view)
    
    completions_to_return = []
    
    for raw in self.raw_completions:
      if raw['def'].lower().startswith(prefix.lower()):
        completions_to_return.append(self.build_completion_from_raw(raw))
    
    # Report time spent building completions before returning
    delta_time_ms = int((time.time() - start_time) * 1000)
    message = 'Jai completion took ' + str(delta_time_ms) + 'ms'
    view.window().status_message(message)
    
    return completions_to_return





