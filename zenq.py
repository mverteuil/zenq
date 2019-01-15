import click
import dotenv
from github import Github
import requests
import terminaltables


# Environment and constants

dotenv.load_dotenv()

ZENHUB_API_ROOT = 'https://api.zenhub.io'
LIST_EPICS_URL = '/'.join((ZENHUB_API_ROOT, 'p1/repositories/{repo_id}/epics'))
GET_EPIC_URL = '/'.join((LIST_EPICS_URL, '{epic_id}'))
GET_BOARD_URL = '/'.join((ZENHUB_API_ROOT, 'p1/repositories/{repo_id}/board'))

# Utilities

GET_BOARD_URL_FMT = GET_BOARD_URL.format
GET_EPIC_URL_FMT = GET_EPIC_URL.format
LIST_EPICS_URL_FMT = LIST_EPICS_URL.format

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


# Entry point

@click.group()
@click.option('--github-api-token', required=True, envvar='ZENQ_GITHUB_API_TOKEN')
@click.option('--zenhub-api-token', required=True, envvar='ZENQ_ZENHUB_API_TOKEN')
@click.pass_context
def cli(ctx, github_api_token, zenhub_api_token):
    ctx.obj['github_client'] = Github(github_api_token)
    ctx.obj['zenhub_headers'] = {'X-Authentication-Token': zenhub_api_token}


# Commands

@cli.command()
@click.option('-r', '--repo-id', envvar='ZENQ_REPO_ID')
@click.pass_context
def get_board(ctx, repo_id):
    """Get details a repository project board"""
    source_repository = get_github_repository(ctx, repo_id)

    url = GET_BOARD_URL_FMT(repo_id=repo_id)
    response = requests.get(url, headers=ctx.obj['zenhub_headers'])
    if response.status_code == 200:
        pipeline_rows = []
        pipelines = response.json()['pipelines']
        for pipeline in reversed(pipelines):
            pipeline_estimate = sum(i['estimate']['value'] for i in filter(lambda i: 'estimate' in i, pipeline['issues']))
            pipeline_rows.append([
                pipeline['name'],
                f'{pipeline_estimate} points',
                f'{len(pipeline["issues"])} issues',
            ])
        pivoted_pipeline_rows = list(zip(*pipeline_rows[::-1]))
        table = terminaltables.SingleTable(pivoted_pipeline_rows, title=source_repository.name)
        click.echo(table.table)
    else:
        click.secho(f'There was an error retrieving your board:\n{response.content}')


@cli.command()
@click.option('-r', '--repo-id', envvar='ZENQ_REPO_ID')
@click.option('-e', '--epic-id')
@click.pass_context
def get_epic(ctx, repo_id, epic_id):
    """Get details on a epic and print to console"""
    source_repository = get_github_repository(ctx, repo_id)

    url = GET_EPIC_URL_FMT(repo_id=repo_id, epic_id=epic_id)
    response = requests.get(url, headers=ctx.obj['zenhub_headers'])
    if response.status_code == 200:
        epic_issue = get_github_issue(ctx, source_repository, epic_id)

        # Write Title
        click.echo('Issue:\n\t#' + click.style(str(epic_issue.number), fg='green') + f' {epic_issue.title}' + '\n')

        # Summary Table
        epic_details = response.json()
        N_A = {'value': 'N/A'}
        summary_table = terminaltables.SingleTable(
            [['Total Points', 'Estimated Points', 'Current Pipeline']] +
            [[epic_details.get('total_epic_estimates', N_A)['value'],
              epic_details.get('estimate', N_A)['value'],
              epic_details['pipeline']['name']]],
            title='Summary'
        )
        click.echo(summary_table.table)

        # Sub-issues Table
        subissue_headings = [['Issue Number', 'Title', 'Estimate', 'Current Pipeline']]
        subissue_rows = []
        for subissue in epic_details['issues']:
            epic_subissue = get_github_issue(ctx, source_repository, subissue['issue_number'])
            subissue_rows.append([
                epic_subissue.number,
                epic_subissue.title[:25],
                subissue.get('estimate', N_A)['value'],
                subissue['pipeline']['name']
            ])
        subissue_table = terminaltables.SingleTable(subissue_headings + subissue_rows, title='Issues')
        click.echo(subissue_table.table)
    else:
        click.secho(f'There was an error retrieving your epic:\n{response.content}')


@cli.command()
@click.option('-r', '--repo-id', envvar='ZENQ_REPO_ID')
@click.pass_context
def list_epics(ctx, repo_id):
    """Show the board for an integrated GitHub repository"""
    source_repository = get_github_repository(ctx, repo_id)

    url = LIST_EPICS_URL_FMT(repo_id=repo_id)
    response = requests.get(url, headers=ctx.obj['zenhub_headers'])
    if response.status_code == 200:
        headings = [['Issue Number', 'Description']]
        body = []
        for epic in response.json()['epic_issues']:
            issue = get_github_issue(ctx, source_repository, epic['issue_number'])
            body.append([issue.number, click.style(issue.title, fg='green')])
        table = terminaltables.SingleTable(headings + body, title='Epics')
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
        table = terminaltables.SingleTable(
            [[repo.id, click.style(repo.name, fg='green')] for repo in repository_list],
            title='Repositories'
        )
        table.inner_heading_row_border = False
        table.inner_row_border = True
        click.echo(table.table)
    else:
        click.secho('No matching repositories found!', fg='red')


if __name__ == '__main__':
    cli(obj={})

