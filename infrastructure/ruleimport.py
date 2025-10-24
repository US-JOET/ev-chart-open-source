import json
import os
import shutil

mapping_file = os.path.join('security_mapping', 'ev_chart_imported_rule_set.json')
src_dir= os.path.join('..', '..', 'aws-guard-rules-registry') #Directory where rules are pulled from
dest_dir= "." #Directory where rules are put

with open(mapping_file, 'r') as file:
    data = json.load(file)

for guard_file in data['mapping']:
    src_file = os.path.join(src_dir, guard_file['guardFilePath'])
    dest_file = os.path.join(dest_dir, guard_file['guardFilePath'])
    
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    
    shutil.copy2(src_file, dest_file)
    
print("Files copied successfully.")
