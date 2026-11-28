# Git Commands Cheat Sheet

Updated for Git 2.56 (September 2026).

## Setup
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main   # default branch name
git config --global pull.rebase true          # rebase on pull instead of merge
git config --global alias.st status           # create a shortcut: git st
git init                    # start a new repo
git clone <url>             # copy a remote repo
```

## Stage and commit (time savers)
```
git add <file>              # stage a file
git add .                   # stage everything
git add -u                  # stage modified/deleted tracked files only
git add -p                  # stage changes interactively, hunk by hunk
git commit -m "message"     # commit staged changes
git commit -am "message"    # stage tracked files AND commit in one step
git commit --amend --no-edit        # add staged changes to last commit, keep message
git commit --amend -m "new msg"     # rewrite last commit message
git status -sb              # short status with branch info
git diff                    # unstaged changes
git diff --staged           # staged changes
git diff --stat             # summary of changed files
```

Note: `git commit -am` does not include new (untracked) files. Use `git add .` first for those.

## Branches
```
git branch                  # list local branches
git branch -a               # list local and remote branches
git branch -vv              # show upstream tracking info
git branch <name>           # create branch
git switch <name>           # switch branch
git switch -c <name>        # create and switch
git switch -                # jump back to the previous branch
git merge <name>            # merge into current branch
git merge --abort           # cancel a conflicted merge
git branch -d <name>        # delete merged branch
git branch -D <name>        # force delete branch
git branch -m <new-name>    # rename current branch
```

## Remotes
```
git remote -v               # list remotes
git fetch                   # download changes, no merge
git fetch --prune           # also remove deleted remote branches locally
git pull                    # fetch and merge
git pull --rebase           # fetch and rebase
git push                    # upload commits
git push -u origin <name>   # push new branch and track it
git push --force-with-lease # safer force push (fails if remote changed)
git push origin --delete <name>   # delete a remote branch
```

## History and search
```
git log --oneline --graph --all     # compact history of all branches
git log -p <file>           # history of a file with diffs
git log --author="name"     # commits by one author
git log -S "text"           # commits that added or removed this text
git show <commit>           # details of a commit
git blame <file>            # who changed each line
git reflog                  # history of where HEAD has been (recovery tool)
git grep "text"             # search tracked files
git shortlog -sn            # commit counts per author
```

## Undo
```
git restore <file>          # discard unstaged changes
git restore --staged <file> # unstage a file
git restore --source=<commit> <file>   # restore a file from any commit
git revert <commit>         # new commit that undoes one
git reset --soft HEAD~1     # undo last commit, keep changes staged
git reset HEAD~1            # undo last commit, keep changes unstaged
git reset --hard HEAD~1     # undo last commit, discard changes (destructive)
git clean -n                # preview untracked files that would be deleted
git clean -fd               # delete untracked files and folders (destructive)
```

Tip: if you lose commits after a reset or rebase, `git reflog` lets you find them and `git reset --hard <hash>` brings them back.

## Stash
```
git stash                   # shelve tracked changes
git stash -u                # include untracked files
git stash push -m "name"    # stash with a label
git stash list              # see all stashes
git stash pop               # restore latest and remove it
git stash apply             # restore latest and keep it
git stash drop              # delete latest stash
```

## Rebase and cherry-pick
```
git rebase <branch>         # replay commits on top of another branch
git rebase -i HEAD~3        # edit, squash, reorder last 3 commits
git rebase --continue       # continue after fixing conflicts
git rebase --abort          # cancel the rebase
git cherry-pick <commit>    # copy one commit onto current branch
```

## Tags
```
git tag                     # list tags
git tag v1.0.0              # lightweight tag
git tag -a v1.0.0 -m "msg"  # annotated tag
git push origin v1.0.0      # push one tag
git push --tags             # push all tags
```

## Useful extras
```
git worktree add ../dir <branch>   # check out another branch in a separate folder
git bisect start                   # binary-search for the commit that broke something
git commit --fixup <commit>        # prepare a fix for an earlier commit
git rebase -i --autosquash <base>  # auto-apply fixup commits
```

---

# GitHub CLI (`gh`) Cheat Sheet

## Setup and auth
```
gh auth login               # sign in to GitHub
gh auth status              # check who you're logged in as
gh auth refresh -s <scope>  # add a permission scope
gh config set editor vim    # set default editor
gh alias set co 'pr checkout'   # create a shortcut: gh co 123
```

## Repos
```
gh repo clone <owner>/<repo>        # clone a repo
gh repo create <name> --public      # create a repo (add --source=. --push to publish current folder)
gh repo fork --clone                # fork and clone
gh repo view --web                  # open repo in browser
gh repo list <owner>                # list repos
gh repo delete <owner>/<repo>       # delete a repo (destructive)
```

## Pull requests
```
gh pr create                        # create a PR (interactive)
gh pr create --fill                 # use commit info for title and body
gh pr create --draft                # open as a draft
gh pr list                          # list open PRs
gh pr status                        # PRs related to you
gh pr view <number> --web           # open a PR in browser
gh pr checkout <number>             # check out a PR locally
gh pr diff <number>                 # see PR changes
gh pr review <number> --approve     # approve (or --request-changes, --comment)
gh pr merge <number> --squash       # merge (or --merge, --rebase)
gh pr merge --auto --squash         # merge automatically once checks pass
gh pr close <number>                # close without merging
gh pr ready                         # mark a draft as ready
```

## Issues
```
gh issue create                     # create an issue (interactive)
gh issue create -t "Title" -b "Body"
gh issue list                       # list open issues
gh issue list --assignee @me        # your issues
gh issue view <number>              # read an issue
gh issue comment <number> -b "text" # add a comment
gh issue close <number>             # close an issue
gh issue develop <number> -c        # create and check out a linked branch
```

## Actions (CI)
```
gh run list                         # recent workflow runs
gh run view <run-id>                # details of a run
gh run view <run-id> --log-failed   # logs of failed steps only
gh run watch                        # follow a run live
gh run rerun <run-id> --failed      # rerun failed jobs
gh workflow list                    # list workflows
gh workflow run <name>              # trigger a workflow manually
gh pr checks                        # CI status of current PR
```

## Releases
```
gh release list                     # list releases
gh release create v1.0.0 --generate-notes   # create a release with auto notes
gh release create v1.0.0 ./file.zip         # attach files
gh release download v1.0.0          # download release assets
```

## Gists
```
gh gist create <file>               # create a gist (add --public to make it public)
gh gist list                        # list your gists
gh gist view <id>                   # view a gist
```

## Search, API and extras
```
gh search repos <query>             # search repositories
gh search issues <query>            # search issues and PRs
gh api repos/<owner>/<repo>         # call any REST API endpoint
gh api graphql -f query='...'       # call the GraphQL API
gh browse                           # open current repo in browser
gh browse <file>                    # open a file in browser
gh codespace create                 # create a codespace
gh extension list                   # list installed extensions
gh extension install <owner>/<repo> # install an extension
gh status                           # your notifications, PRs and issues
gh --help                           # help for any command (works on subcommands too)
```

## Handy combos
```
git switch -c fix-bug && git commit -am "Fix bug" && git push -u origin fix-bug && gh pr create --fill
gh pr checkout 123 && gh pr diff        # review a PR locally
gh run watch && gh pr merge --squash    # wait for CI, then merge
```
