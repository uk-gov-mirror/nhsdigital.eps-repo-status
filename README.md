EPS REPO STATUS
================

This repo contains code that generates data from other repos which it then displays on github pages. The kind of data it includes is number of pull requests, deployment status, security alerts etc

Users with access can view the reports by going to: [https://nhsdigital.github.io/eps-repo-status](https://nhsdigital.github.io/eps-repo-status)

## Design
The main branch contains a python module under packages/get_repo_status.   
The main entry point is cli.py.   
The script loops through a list of all EPS repos and for eaoch one, calls various github apis (using pygithub) to get all the necessary information.   
It then writes all the information to a json file.   

There is a github action called update_repo_status_data that runs every hour and on demand.   
This action 
- generates a github token based off app id and a pem file stored in github secrets. These are from a github app that has been installed to all repos that we need to get data from
- runs the python module
- commits the json file to _data in gh-pages branch.   

Github pages is configured to build off the gh-pages branch.   
This branch contains several jekyll html templates which read data from the _data folder and create html pages which are then published.   

The project also contains standard eps Makefile targets such as make lint, make install, make test etc.
The project uses standard eps common workflows to run quality checks on pull requests and merges to main, and tag release common workflow to create a release on a merge to main.


## Testing data generation locally
To test the data generation locally, create a branch from main.   
Then authenticate to github using
```
make github-login
```
You can then run the script using
```
make run-get-repo-status
```
This produces a file in /tmp/repo_status_export.json


### Testing github pages changes
To test changes to github pages, checkout gh-pages branch.   
Setup jekyll locally using
```
make install-jekyll
```
And then run the website using
```
make run-jekyll
```
The website can then be viewed at http://localhost:4000/. Any changes to local files will result in a regeneration of the website
