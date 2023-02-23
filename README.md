# BODS

Bus Open Data Service

## Contributing

Please read the [CONTRIBUTING.md](CONTRIBUTING.md) document if you wish to setup
a development environment.

## Deployment

We now have 4 environments:

- dev
- test
- uat
- prod

Your branch should be merged in the following order:
Feature_branch -> dev -> test -> main -> tagging (with the relevant version)

- The dev branch deploys into the dev environment
- The test branch deploys into the test environment
- The main branch deploys into the uat environment
- Tags deploy to the prod environment

When pushing to the dev branch, an image will be built and pushed up the ECR,
tagging it with the version specified in 'version.txt' (so make sure you change
this when pushing your code up, otherwise the pipeline will not be triggered).
The services will then be updated to use this latest version.

When pushing to the other environments (test, uat or prod), it will use the version.txt
file to find the image version and update the services accordingly.
All deployments are automated other than the prod deployment, which requires an
approval from the KPMG infrastructure team.

## HotFix Deployment

### Step 1

Create a pull request from your branch into test, obtain approval and merge.
This will trigger the test pipeline.
The test pipeline should fail as the image does not exist.

### Step 2

Navigate to the hotfix pipeline and trigger it from the test branch. This will
trigger the build and will take around 1:30 minutes to complete.
