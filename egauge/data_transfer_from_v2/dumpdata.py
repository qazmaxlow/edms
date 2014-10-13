#!/usr/bin/python

import subprocess
import os

os.umask(000)
# range should be xrange(1, 78)
for school_id in [22, 76]:
    db_name = 'school%d'%school_id
    target_path_dir = os.path.join('db_dump_csv', db_name)
    os.mkdir(target_path_dir)
    for table_name in ['min', 'hour', 'day', 'week', 'month', 'year']:
        command = 'mysqldump --tab=%s --order-by-primary --no-create-db --no-create-info --fields-terminated-by=\',\' --fields-optionally-enclosed-by=\'"\' %s %s -u root -pwneriqle -h 127.0.0.1'%(target_path_dir, db_name, table_name)
        subprocess.call(command, shell=True)
