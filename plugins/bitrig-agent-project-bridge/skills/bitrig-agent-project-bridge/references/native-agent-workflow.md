# Native Agent Workflow Notes

## Why native creation is required

Bitrig Remote reads native Agent project state. Manually inserting rows into `app.bitrig.AppIntents.ProjectIndex` can make a row appear briefly, but Bitrig prunes records that are not backed by a real Agent project. A durable Agent project has:

- An entry in `~/Library/Bitrig/Projects.json`.
- A folder at `~/Library/Bitrig/Projects/<project-id>/`.
- A `Project.json` XcodeGen-style project specification.
- A `BitrigAgent.json` metadata file.
- A visible `source=agent` row in `app.bitrig.AppIntents.ProjectIndex` after Bitrig finishes creating or saving the project.

## Reliable creation path

Use Bitrig's own Agent New Project composer:

1. Open Bitrig.
2. Select Agent in the project list.
3. Use the `+` button or `File > New Project`.
4. Confirm the composer label says `Agent`.
5. Paste the generated project prompt.
6. Submit and wait for Bitrig to finish editing and building.
7. Close the project window back to the Agent list if the index has not refreshed.

## False positives

- A `classic` row named like the target project does not satisfy Bitrig Remote Agent.
- A generated project without `BitrigAgent.json` is suspect.
- A project visible only until Bitrig relaunches was probably not native.
- `BUILD SUCCEEDED` from an unrelated Xcode project does not prove Bitrig Remote can see the Agent project.

## Recovery

If Bitrig creates the right Agent project but the name is still `New Project`, use Bitrig chat in that project and ask it to rename the target and project to the desired name. Then re-run `verify_bitrig_agent_project.py --name "Name"`.

If the generated shell fails to build, inspect Bitrig's on-screen build error first. Fix the files under `~/Library/Bitrig/Projects/<project-id>` only after identifying the error, then let Bitrig rebuild.
