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

### Next.js frontend (frontend_v2)

The Next.js app in `bods-nextjs/` is deployed as a separate ECS service (`frontend_v2`) alongside the existing Django frontend.
In the current setup this is driven from the `DBODS-679/bods-two` branch (or a manual `workflow_dispatch` of the `nextjs` service) via `.github/workflows/dev_deployment.yml`.

Traffic still defaults to the django frontend. To use the new Next.js service, send the `use-frontend-two` request header (for example with a
browser extension such as Requestly, or via curl):

```bash
curl -H 'use-frontend-two: true' https://www.dev.bus-data.dft.gov.uk/
```

## HotFix Deployment

### Step 1

Create a pull request from your branch into test, obtain approval and merge.
This will trigger the test pipeline.
The test pipeline should fail as the image does not exist.

### Step 2

Navigate to the hotfix pipeline and trigger it from the test branch. This will
trigger the build and will take around 1:30 minutes to complete.
