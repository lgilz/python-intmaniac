from intmaniac import testrun as tr

import yaml

testrun_configs = {
    'default': {
        'image': 'my/testimage:latest',
        'pre': 'sleep 10',
        'commands': 'cmd1',
        'links': ['two'],
        'environment': {
            'TARGET_URL': 'rsas',
        }
    },
    'nocommands': {
        'image': 'my/testimage:latest',
        'pre': 'sleep 10',
        'links': ['two'],
        'environment': {
            'TARGET_URL': 'rsas',
        }
    },
    'twocommands': {
        'image': 'my/testimage:latest',
        'pre': 'sleep 10',
        'links': ['two'],
        'commands': ['cmd1', 'cmd2'],
        'environment': {
            'TARGET_URL': 'rsas',
        }
    },
}

v2_config_minimal_rep_str = """
---
version: 2
compose_template: /template0

tester_config:
  image: %%MY_IMAGE%%
  links: ["cvs:cvs"]
  environment:
    foo: bar
"""

v2_config_minimal_str = """
---
version: 2
compose_template: /template0

tester_config:
  image: my/image
  links: ["cvs:cvs"]
  environment:
    foo: bar
"""
v2_config_minimal = yaml.safe_load(v2_config_minimal_str)

v3_config_rep_str = """
---
version: 3
compose_templates: {template0: /template0}

tester_configs:
  tester_def0:
    image: %%MY_IMAGE%%
    links: ["cvs:cvs"]

tests:
  test0:
    compose_template: template0
    tester_config: tester_def0
"""

v3_config_minimal_str = """
---
version: 3
compose_templates: {template0: /template0}

tester_configs:
  tester_def0:
    image: image:latest
    links: ["cvs:cvs"]

tests:
  test0:
    compose_template: template0
    tester_config: tester_def0
"""
v3_config_minimal = yaml.safe_load(v3_config_minimal_str)

v3_config_onecommand_str = """
---
version: 3
compose_templates: {template0: /template0}

tester_configs:
  tester_def0:
    image: image:latest
    links: ["cvs:cvs"]
    commands: ["cmd1", "cmd2"]

tests:
  test0:
    compose_template: template0
    tester_config: tester_def0
"""
v3_config_onecommand = yaml.safe_load(v3_config_onecommand_str)

v3_config_0 = yaml.safe_load("""
---
environments:
  env0:
    one: two
  env1:
    thr: for

compose_templates:
  template0: /template0
  template1: /template1

tester_configs:
  tester_def0:
    image: image:latest
    links: ["cvs:cvs"]
    commands: command0
  tester_def1:
    image: image:earliest
    links: ["image:link"]
    commands: command1
  tester_def2:
    image: image:middle
    links: ["wo:ho"]
    commands: command2

tests:
  test0:
    compose_template: template0
    tester_config: tester_def0
    environment: env0

  test1:
    compose_templates: [template0, template1]
    tester_configs: [tester_def1, tester_def2]
    environments: [env0, env1]

""")


# all of those need "-e cmd=too"
tester_config_test01 = yaml.safe_load("""
---
image: image:latest
links: ["cvs:cvs"]
commands: [["command0"]]
environment: {one: two, cmd: too}
""")

# dev1, env0
tester_config_test11_and_13 = yaml.safe_load("""
---
image: image:earliest
links: ["image:link"]
commands: [["command1"]]
environment: {one: two, cmd: too}
""")

# dev1, env1
tester_config_test12_and_14 = yaml.safe_load("""
---
image: image:earliest
links: ["image:link"]
commands: [["command1"]]
environment: {thr: for, cmd: too}
""")

# dev2, env0
tester_config_test15_and_17 = yaml.safe_load("""
---
image: image:middle
links: ["wo:ho"]
commands: [["command2"]]
environment: {one: two, cmd: too}
""")

# dev2, env1
tester_config_test16_and_18 = yaml.safe_load("""
---
image: image:middle
links: ["wo:ho"]
commands: [["command2"]]
environment: {thr: for, cmd: too}
""")


# we ASSUME that the tests have /<test_name> as their compose template
v3_config_0_test01 = tr.Testrun('test0_1', '/template0', **tester_config_test01)
v3_config_0_test11 = tr.Testrun('test1_1', '/template0', **tester_config_test11_and_13)
v3_config_0_test12 = tr.Testrun('test1_2', '/template0', **tester_config_test12_and_14)
v3_config_0_test13 = tr.Testrun('test1_3', '/template0', **tester_config_test15_and_17)
v3_config_0_test14 = tr.Testrun('test1_4', '/template0', **tester_config_test16_and_18)
v3_config_0_test15 = tr.Testrun('test1_1', '/template1', **tester_config_test11_and_13)
v3_config_0_test16 = tr.Testrun('test1_2', '/template1', **tester_config_test12_and_14)
v3_config_0_test17 = tr.Testrun('test1_3', '/template1', **tester_config_test15_and_17)
v3_config_0_test18 = tr.Testrun('test1_4', '/template1', **tester_config_test16_and_18)

mock_testruns = [
    v3_config_0_test01,
    v3_config_0_test11,
    v3_config_0_test12,
    v3_config_0_test13,
    v3_config_0_test14,
    v3_config_0_test15,
    v3_config_0_test16,
    v3_config_0_test17,
    v3_config_0_test18,
]


def get_test_tr(config, name="_DEFAULT_", template='/hoo/ha'):
    if name == "_DEFAULT_":
        name = config
    return tr.Testrun(name, template, **testrun_configs[config])
