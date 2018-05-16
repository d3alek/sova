from pathlib import Path
import datetime

from ruamel.yaml import YAML
import subprocess

VERSION='0.2'

def load():
    model = {}
    yaml = YAML()
    for entity_path in Path('garden').iterdir():
        entity = entity_path.stem
        if entity == '.git':
            continue
        for instance_path in entity_path.iterdir():
            instance = instance_path.stem
            model.setdefault(entity, {})[instance] = yaml.load(instance_path.read_text())

    return model

def save(model, what, author, dryrun=False, **commit_params):
    yaml = YAML()
    for entity, instances in model.items():
        for instance, value in instances.items():
                file_path = (Path('garden') / entity / instance).with_suffix('.yaml')
                if dryrun:
                    print("dryrun: Writing to %s:\n%s" % (file_path, value))
                else:
                    with file_path.open('w') as f:
                        yaml.dump(value, f)

    ret = subprocess.run(['git', '-C', 'garden', 'status', '-s'], stdout=subprocess.PIPE)
    result = ret.stdout.decode('utf-8')

    if not result:
        print("No changes to commit.")
        return

    print(result)

    if dryrun:
        print("Stopping because this is dryrun")
        return

    ret = subprocess.run(['git', '-C', 'garden', 'add', '--all'], stdout=subprocess.PIPE)
    result = ret.stdout.decode('utf-8')

    assert not result, "Expecting no stdout from %s" % ret

    message = what + '\n\n' 
    message += '\n'.join(['%s: %s' % (key, value) for key, value in sorted(commit_params.items())])
    author = "{name} <{email}>".format(**author)
    ret = subprocess.run(['git', '-C', 'garden', 'commit', '--author', author, '-m', message], stdout=subprocess.PIPE)
    result = ret.stdout.decode('utf-8')
    print(result)

def help_adding(entity_type):
    found = list(filter(lambda f: f.stem == entity_type, Path('templates').iterdir()))
    assert found, "Did not find template for %s" % entity_type
    return found[0].read_text()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()

    model = load()

    save(model,
         author={
             'name': 'sova v' + VERSION,
             'email': 'sova@otselo.eu'},
         what='normalizing repo',
         dryrun=args.dryrun)
