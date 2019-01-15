import click
import dotenv
from github import Github
import requests
import terminaltables

dotenv.load_dotenv()

ZENHUB_API_ROOT = 'https://api.zenhub.io'
EPICS_URL_FMT = '/'.join((ZENHUB_API_ROOT, 'p1/repositories/{repo_id}/epics')).format


def get_github_repository(ctx, repo_id):
    try:
        return ctx.obj['github_client'].get_repo(int(repo_id))
    except Exception as e:
        ctx.fail(click.style(e.data['message'], fg='red'))


def get_github_issue(ctx, repo, issue_id):
    try:
        return repo.get_issue(int(issue_id))
    except Exception as e:
        ctx.fail(click.style(e.data['message'], fg='red'))


@click.group()
@click.option('--github-api-token', required=True, envvar='ZENQ_GITHUB_API_TOKEN')
@click.option('--zenhub-api-token', required=True, envvar='ZENQ_ZENHUB_API_TOKEN')
@click.pass_context
def cli(ctx, github_api_token, zenhub_api_token):
    ctx.obj['github_client'] = Github(github_api_token)
    ctx.obj['zenhub_headers'] = {'X-Authentication-Token': zenhub_api_token}


@cli.command()
@click.option('-r', '--repo-id', envvar='ZENQ_REPO_ID')
@click.pass_context
def list_epics(ctx, repo_id):
    """Show the board for an integrated GitHub repository"""
    source_repository = get_github_repository(ctx, repo_id)

    url = EPICS_URL_FMT(repo_id=repo_id)
    response = requests.get(url, headers=ctx.obj['zenhub_headers'])
    if response.status_code == 200:
        headings = [['Ticket ID', 'Description']]
        body = []
        for epic in response.json()['epic_issues']:
            issue = get_github_issue(ctx, source_repository, epic['issue_number'])
            body.append([issue.number, click.style(issue.title, fg='green')])
        table = terminaltables.SingleTable(headings + body)
        table.inner_row_border = True
        click.echo(table.table)

    else:
        click.secho(f'There was an error retrieving your epics:\n{response.content}')


@cli.command()
@click.option('-o', '--match-owner')
@click.option('-n', '--filter-name', callback=lambda ctx, opts, value: value.lower() if value else value)
@click.pass_context
def list_repo_ids(ctx, match_owner=None, filter_name=None):
    """List and optionally filter the repositories associated with your ZENQ_GITHUB_API_TOKEN"""
    repository_list = ctx.obj['github_client'].get_user().get_repos()

    if match_owner:
        repository_list = [repo for repo in repository_list if match_owner == repo.owner.login]

    if filter_name:
        repository_list = [repo for repo in repository_list if filter_name in repo.name.lower()]

    if repository_list:
        click.echo('The following repositories were discovered:')
        table = terminaltables.SingleTable([[repo.id, click.style(repo.name, fg='green')] for repo in repository_list])
        table.inner_heading_row_border = False
        table.inner_row_border = True
        click.echo(table.table)
    else:
        click.secho('No matching repositories found!', fg='red')


if __name__ == '__main__':
    cli(obj={})

