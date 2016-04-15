
testrun_configs = {
    'default': {
        'image': 'my/testimage:latest',
        'pre': 'sleep 10',
        'commands': 'cmd1',
        'links': ['two'],
        'environment': {
            'TARGET_URL': 'rsas',
        }
    }
}
