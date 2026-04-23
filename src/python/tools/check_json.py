import json
try:
    with open('/workspace/rules.json') as f:
        data = json.load(f)
    print('JSON valid, {} rules'.format(len(data)))
    for i, r in enumerate(data):
        print('  Rule {}: action={} priority={}'.format(i+1, r.get('action_name'), r.get('priority', 'N/A')))
except Exception as e:
    print('ERROR:', e)
