Spec and template for clouducer.

# clouducer spec

As of Feb 2020, clouducer is an interface spec for deploying cloud resources.

- The module has a "$TOPLEVEL/deploy/deploy" executable and "$TOPLEVEL/deploy/deployment_vars.json" for configuration,
  where "$TOPLEVEL" is the top level directory of the git repo.
- The deploy executable takes the subcommands `init`, `apply`, and `destroy`.

In practice, clouducer has been used with zsec-aws-tools and extensions to deploy cloud resources,
but the above spec leaves open other possibilities. This template and the rest
of the documentation below uses zsec-aws-tools and extensions.

## clouducer/zsec-aws-tools spec

- Should only depend on python and virtualenv. As of v0.1.0 of this template, that is python 3.8 and compatible versions.
- `deploy init` should install all dependencies in a virtual env called `deployment_env`. The `requirements.txt` file
  should contain python lib dependencies.
- `deploy apply` and `deploy destroy` should be idempotent.
- `deploy apply` and `deploy destroy` run `main.py apply`, and `main.py destroy` using the virtualenv in
  `deployment_env`.


# Important note on ztid (zsec-tools ID)

In this "main.py", notice that each resource has a "ztid".
A ztid maps a resource to the code.
Make sure you generate a new UUID for each ztids. It is best to use lower case for convenient grepping.
If two pieces of code have the same ztid, this will cause undefined behavior.


# Dependencies

Requires python 3.8 environment with virtualenv. Installation is included in "init" step (see below).


# Things to fill in

- Need to configure the secrets management for codebuild. See the top of `codebuild/buildspec.yml`.
- Need to fill in the `codebuild/known_hosts`.
- Need to fill in the `codebuild/ssh_config`.
- Customize the `deploy/configure` script.


# How to use this template as the basis for your own module

- All places that you must change in your fork have the word "WARNING" in a comment next to them.
- Change the value of `manager` in `main.py`
- Change the value of all `ztid` attributes.
- Make sure the `gc_scope` is appropriate to your needs. In the template, it is set to the manager
  and the account. If you intend your module to define resources accross many accounts in a single
  deployment, you should not specify an account in the `gc_scope`.

# How to deploy

1. Go to `deploy/`
2. Configure `deployment_vars.json`, like below. You must define the profile
   where the resources will be deployed.

   Hint: You may find it useful to differentiate configurations with the `--laptop-test` flag.

2. Run `./deploy init`
3. Run `./deploy apply`

This should deploy a lambda, database, and lambda role.

You can run `./deploy destroy` when you're done with it.


# Operation

- You can configure "deployment_vars.json" for local deployment. Useful for development,
  or deployment from EC2.
- "codebuild/buildspec.yml" can be included for use with AWS Codebuild.


# Development Guidance

`main.py` should be used as configuration, as opposed to a library. Any parts of configuration that need to
be machine writable should be placed in `deployment_vars.json` and read in by `main.py`.

In fact all of the code in `main.py` should be configuration or convenience utilities. Library
code should be moved to another package.

Those who are used to only using serialization formats for configuration may be
surprised by and object to "hard coded" values in `main.py`. However, when viewed as configuration,
a low level of abstraction in `main.py` is acceptable and even desired.

That said, account numbers should generally be considered even "softer" configuration than the code in `main.py`
and should be placed in `deployment_vars.json`.


