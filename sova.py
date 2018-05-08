from pathlib import Path
import textwrap
import re
import io 
import datetime

from ruamel.yaml import YAML
import subprocess

VERSION='0.1'

def indent(amount, text):
    return textwrap.indent(text, amount*' ')

def parse(entity, one_yaml):
    parsed = ""
    instances = [*entity.iterdir()]
    if len(instances) > 0:
        parsed += indent(0, entity.stem + ':') + '\n'
        for instance in instances:
            parsed += indent(4, instance.stem + ":") + '\n'
            parsed += indent(8, instance.read_text()) + '\n'

    return parsed

def load():
    one_yaml = ""
    entities = {e.stem: e for e in Path('garden').iterdir()}
    one_yaml += (
            parse(entities.pop('plots'), one_yaml)
        + parse(entities.pop('beds'), one_yaml)
        + parse(entities.pop('plants'), one_yaml)
        + parse(entities.pop('plantings'), one_yaml)
        + parse(entities.pop('knowledge'), one_yaml))

    entities.pop('.git')

    if entities:
        raise RuntimeError("Remaining unparsed entities:" + str(entities))

    one_yaml = one_yaml.replace('\t', 2*' ')
    yaml = YAML()
    model = yaml.load(one_yaml)
    return model

def split_into_instance_dumps(s):
    instance_dumps = []
    entity_matches = [*re.finditer('^([\w-]+):\n', s, flags=re.MULTILINE)]

    for entity_match, next_entity_match in zip(entity_matches, entity_matches[1:] + [None]):
        entity = entity_match.group(1)
        content_end = next_entity_match.start() if next_entity_match else None
        #TODO fix parsing here
        entity_content = textwrap.dedent(s[entity_match.end():content_end])
        instance_matches = [*re.finditer('^([\w-]+):\n', entity_content, flags=re.MULTILINE)]
        if len(instance_matches) < 1:
            raise RuntimeError("Expected at least 1 instance in %s: %s" % (entity_match, entity_content))
        for instance_match, next_instance_match in zip(instance_matches, instance_matches[1:] + [None]):
            instance = instance_match.group(1)
            content_end = next_instance_match.start() if next_instance_match else None
            instance_content = textwrap.dedent(entity_content[instance_match.end():content_end]).strip()

            instance_dumps.append((entity, instance, instance_content))

    return instance_dumps

def save(model, what, author, dryrun=False, **commit_params):
    yaml = YAML()
    output = io.StringIO()
    yaml.dump(model, output)
    s = output.getvalue()

    instance_dumps = split_into_instance_dumps(s)

    for entity, instance_name, content in instance_dumps:
        file_path = (Path('garden') / entity / instance_name).with_suffix('.yaml')
        if dryrun:
            print("dryrun: Writing to %s:\n%s" % (file_path, content))
        else:
            with file_path.open('w') as f:
                f.write(content)

    ret = subprocess.run(['git', '-C', 'garden', 'status', '-s'], stdout=subprocess.PIPE)
    result = ret.stdout.decode('utf-8')

    if not result:
        print("No changes to commit.")
        return

    print(result)

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
    model = load()

    save(model,
         author={
             'name': 'sova v' + VERSION,
             'email': 'sova@otselo.eu'},
         what='normalizing repo')
