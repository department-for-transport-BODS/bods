# Contributing to BODS

## BODS Git Flow

For BODS development we use [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
as our development workflow.
In this section I will take you through how use this workflow for BODS.

In BODS we have 2 protected branches `master` and `develop`.
These branches should track 2 of our 3 environments `production` and `internal` respectively.
The third environment, `staging` should track a `release` branch.

## Feature Development

When working on a feature the first step is finding a ticket to work on. Go to the
[BODS JIRA](https://itoworld.atlassian.net/jira/software/c/projects/BODP/issues?filter=allissues)
and claim by setting yourself as the `Assigne`, also make a note of the issue ID
and the issue title.

### Creating a feature branch

First, ensure you are currently in the `develop` branch of the project. Make a "feature"
branch including the issue ID and title in the branch name. E.g. issue BODP 1234
with title "Add wigdet to timetables list page" would be created as follows;

```sh
git checkout -b feature/BODP-1234-timetable-list-widget
```

In this example I have used dashes (`-`), you can also use (`_`) to separate
words, ultimately it doesn't matter as these branches should be short lived.

You should immediately push your local branch to the remote repo and open a
merge request.

```sh
git push origin feature/BODP-1234-timetable-list-widget
```

When you push this branch the remote Gitlab repository will respond with
a link to quickly open the merge request. I highly recommend you open
the merge request immediately, ensure a [WIP](https://about.gitlab.com/blog/2016/01/08/feature-highlight-wip/)
is added to the merge request to prevent accidental merging before the feature
is finished.

### Working on a feature

You are now ready to make changes to the code, remember to commit early and often.

```sh
# Do something awesome
git add somefile.py
git commit
git push origin feature/BODP-1234-timetable-list-widget
```

BODS will use [pre-commit](https://pre-commit.com/) to ensure your code meets
coding standards. Remember to push your changes so that merge requet is
updated.
If you suspect that your merge request will grow to incorporate a large
number of changes, see if you can break it into merge requests that
are logically consistent.
If there is no avoiding a large merge request now might be a good time
to assign a reviewer so they have lots of time to review your code.
(See below)

### Get your feature reviewed

Depending on how many people are working on BODS you may be able to
choose from a number of people to review your code.
If you are modifying an existing feature try and find out who the
original author of the code was and asking them to review your
changes.
If you are working on a new feature you can choose the most appropriate
person.
When you have decided on someone assign the Gitlab issue to them of
leave an `@username` comment asking them to review.

### Merging your feature

Your code should not be merged into `develop` until it has been given
the :thumbsup: by another developer (the merge request should literally
have a thumbs up).

When you're ready to merge, click the `Merge` button in the Gitlab
merge request page, (also ensure the `Delete source branch` checkbox is
ticked).

### Clean up your local branchs

Feature branches are short lived, now that your feature is in develop
delete your local feaure branch.

```sh
git branch -d feature/BODP-1234-timetable-list-widget
```

## Releasing a version of BODS
