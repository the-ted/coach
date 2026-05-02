Please spin up a team of developers to implement each of the plans in plans/.

Assign one developer to each report. However, don't try to do too much at one time - prioritize the work so that changes unlikely to cause conflicts are worked on in parallel, and changes that may conflict are done in serial. Tell each developer to use the /implement_platform command skill. Also, tell each developer to manually verify their changes themselves using playwright-cli and associated skills, ensuring they are running it in a dedicated session to avoid conflicts. Tell each developer the anthropic api key environment variable ANTHROPIC_API_KEY (read it yourself in bash) so they have it if they need it.

Your job is to orchestrate these developers, merge their changes together, manage worktrees and conflicts, and perform manual verification.

After all developers finish their work, perform some high-level manual verification steps yourself via playwright-cli.

Also, check and confirm that all tests still pass after all developers have completed their work.

After you are done, make a git commit with all of these changes, push it, and open a PR. Link your PR to the github issues (you can probably find them in research/ if you need to).

Then, mark the initial issues as "completed" in github.
