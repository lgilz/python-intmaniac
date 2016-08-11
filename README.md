# INTManiac

This python tool enables you to run a test program against a set of containers to smoke- / integration- / acceptance-test your program. `docker-compose` is used to create your program environment stack, while `docker` is used to run a container with a test program against that stack.

You can run a matrix test, which means you can check several combinations of containers with each other.

This tool is available as docker container as well. There is a constantly updated docker container available under:

* `quay.io/flypenguin/intmaniac`


## How this works

For most products you want to test them embedded in a system of connected components. For example if you use a database, it might be good to know with which versions of the database your product works, or that your latest build has still the same API functionality than your stable branch.

`intmaniac` enables you to write a parameterized `docker-compose` template which describes your full test environment, and then run tests against it. It uses a `docker-compose` template to create your application stack, and then uses `docker` to run a container with a test program. The container is linked against your application stack using the `links` key in the `tester_config(s)`, so everything happens completely separate from your actual host network.

All tests are executed in sequence.


## TODO

A lot basically ...

* Unit tests are not too good (ha-ha...)
* If a command blocks forever intmaniac will also block forever
* More information about service outputs would also be nice (currently it's ONLY the tester which is printed, this will change soon I guess)
* The text output sucks. Seriously. I use it with TeamCity only right now, so I did not put much effort into this.
* The code quality is ... so-so, I guess. Much better than before, though. :)
* And a lot more probably.


## Super-quick-start

    $ mkvirtualenv intmaniac
    $ pip install intmaniac
    
    # now run with the intmaniac.yaml file in the current directory
    $ intmaniac

    # or maybe even with an environment variable set
    $ intmaniac -e TMP_IMAGE=my/tmp:image


## Configuration reference


### intmaniac.yaml

Use version 2 for a single test run (one testing container in one docker-compose setup).

```yaml
---
version: 2          # can be string or int, for ONE single test combination


# required, if path is relative it will be interpreted as relative
# to this file
compose_template: "here/be_dragons.yml"


# required, one must be present.
tester_config:

  # required
  image: my/image:latest

  # required, format: [linked_service_from_compose_file, ...]
  # a service "myservice" will be linked into the test container under
  # that name (so that the host name "myservice" will resolve)
  links: []

  # optional, can be string, list of strings, list of lists of strings
  commands: "..."       # executed in the tester container
  pre: "..."            # executed on the local machine
  post: "..."           # same. (example: "sleep 10")

  # optional, format { key: value }
  environment: {}

  # optional. true / false. default is false.
  allow_failure: false  # allow test to fail

  # optional, boolean, default is true.
  pull: true            # pull containers before running
```

Use version 3 for a matrix test (multiple environments, set-ups, tests, etc.). The (non-working) example below will create two tests. Basically every possible combination is created for each test and then run.

```yaml
---
version: 3          # can be string or int, allows for matrix test

# required, must have one entry, format: { name: template_path }
compose_templates:
  my_template: "..."        # as above

# required, must have one entry. format: { name: tester_config }
# tester_config is the same structure as defined above.
# if there is an environment definition it is merged UNDER the environment
# defined in the "tests" section (lower precedence)
tester_configs:
  my_tester: {}             # as above
  my_other_tester: {}       # as above

# optional.
environments:
  my_environment: {}        # as above

# required, must have one entry. see below for example
tests:
  default:

    # required. either "string" or [string, ...]
    # the key can also be named "tester_configs". DO NOT define both.
    tester_config: [my_tester, my_other_tester]

    # required. either "string" or [string, ...]
    # the key can also be named "compose_templates". DO NOT define both.
    compose_template: my_template

    # optional. either "string" or [string, ...]
    # the key can also be named "environments". DO NOT define both.
    environment: my_environment
```

## Full example, with docker-compose file

```yaml
---
# docker-compose-pg.yml

test-me:
  image: my_company_hub/%%TEST_CONTAINER%%
  environment:
    - DB=postgresql://db:5432
  links:
    - db:db

db:
  image: postgres:%%PG_VERSION%%

---
# docker-compose-mongo.yml

test-me:
  image: my_company_hub/%%TEST_CONTAINER%%
  environment:
    - DB=mongodb://db:27019
  links:
    - db:db

db:
  image: mongo:%%MONGO_VERSION%%

---
# intmaniac.yaml

version: 3

compose_templates:
  default: docker-compose-pg.yml
  next: docker-compose-mongo.yml

environments:
  postgres93: { PG_VERSION: "9.3" }
  postgres94: { PG_VERSION: "9.4" }
  postgres95: { PG_VERSION: "9.5" }
  mongodb24:  { MONGO_VERSION: "2.4" }
  mongodb32:  { MONGO_VERSION: "3.2" }


tester_configs:
  standard_tester:
    image: myhub.com/myproduct/acceptance:production
    links: ["test-me:testservice"]
    environment:
      TEST_URL: http://testservice:80
  prerelease:
    image: myhub.com/myproduct/acceptance:beta
    links: ["test-me:testservice"]
    allow_failure: true
    environment:
      TEST_URL: http://testservice:80

tests:
  databases:
    compose_template: default
    tester_config: [standard_tester, prerelease]
    environments: [ postgres93, postgres94, postgres95 ]
  prerelease-pg:
    compose_template: default
    tester_config: prerelease
    environment: [postgres94,postgres95]
  prerelease-mongo:
    compose_template: next
    tester_config: prerelease
    environment: [mongo24,mongo32]
```
In this case it is assumed that `TEST_CONTAINER` comes from a commandline `-e TEST_CONTAINER=...` setting.

Now you should have an idea about how this works.
