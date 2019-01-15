import functools
import os

import click
import requests


    #api_get = functools.partial(requests.get, headers={'X-Authentication-Token': zenhub_api_key})

@click.group()
@click.option('--zenhub-api-key')
@click.pass_context
def cli(ctx, zenhub_api_key):
    ctx.obj['zenhub_api_key'] = zenhub_api_key
    click.echo('hello world')

@cli.command()
@click.option('--github-api-key')
def list_repo_ids(github_api_key):



if __name__ == '__main__':
    zenq(auto_envvar_prefix='ZENQ')

