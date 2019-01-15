ZenQ
----

Query ZenHub for Story Points


Instructions
------------

   - Generate a ZenHub API key at https://app.zenhub.com/dashboard/tokens
   - Generate a GitHub Personal Access Token at https://github.com/settings/tokens
       - You only need to provide `repo:*` scope
   - Set environment variables or use `.env` file (you can pass these as options as well):
       - ZENQ_GITHUB_API_TOKEN (required)
       - ZENQ_ZENHUB_API_TOKEN (required)
   - Install using poetry
       - `poetry install`
   - Enjoy
       - `./zenq.py list-repo-ids`

Optional:
Set the ZENQ_REPO_ID environment variable to save yourself from entering it with the rest of the commands

Commands
--------

   - `./zenq.py get-board -r <repo_id>`: retrieve ZenHub board overview for repository
   - `./zenq.py list-epics -r <repo_id>`: retrieve a list of ZenHub epics for repository
   - `./zenq.py get-epic -r <repo_id> -e <epic_id>`: retrieve the status of a ZenHub epic
   - `./zenq.py list-repo-ids`: retrieve a list of repository ids
   - `./zenq.py list-repo-ids -o mverteuil`: retrieve a list of repository ids filtered by owner mverteuil (exact match)
   - `./zenq.py list-repo-ids -o mverteuil -n octo`: retrieve a list of repository ids filtered by owner mverteuil (exact match) and repository name 'octo' (fuzzy match)
   - `./zenq.py list-repo-ids -n octo`: retrieve a list of repository ids filtered by repository name 'octo' (fuzzy match)
   
