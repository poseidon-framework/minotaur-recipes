<!--
# poseidon-framework/minotaur-recipes package request

Hello there!

Thanks for suggesting a new publication to add to the Poseidon Minotaur Archive!
Please ensure you are completing all the TODOs outlined in these comments for each section.
-->

Linked to #XXX <!-- TODO: Please link the issue requesting the package here. -->

## PR Checklist

- [ ] The PR title is in the format `Add/Update package: {package_name}`.
- [ ] The PR description includes a link to the issue requesting the package its
      update. (Add to `Linked to #XXX` above.)

## If adding or updating a package:

### SSF file Todo list

- [ ] This PR contains a sequencingSourceFile (`.ssf`) for the requested
      package.
- [ ] The name of the `.ssf` file(s) matches the package name (i.e.
      `packages/2023_my_package/2023_my_package.ssf`).
- [ ] The `.ssf` file MUST contain a new line at the end of the file.
      A check for this exists in the CI. This check should pass before
      you continue with this list.
- [ ] I confirm that the `poseidon_IDs`, `udg`, and `library_built` are filled
      and correct.
- [ ] I made sure to leave `notes` where necessary to explain any special
      cases/judgement calls made for data entries.

### Include a Janno file

It is recommended that you include a janno file for the requested package to the PR.
While optional, recipes that include a janno file will be prioritised for processing.

- [ ] (optional) This PR contains a janno file (`.janno`) for the requested
      package.
  - [ ] The name of the `.janno` file(s) matches the package name (i.e.
            `packages/2023_my_package/2023_my_package.janno`).
  - [ ] The `.janno` file contains one record per poseidon_id specified in the SSF file.

### Recipe creation and validation

- [ ] Comment `@delphis-bot create recipe` to this pull request to awaken
      Poseidon's trusty helper. (This should be repeated whenever changes are
      made to the SSF file contents).

After a few second, Delphis-bot will add a number of files to the PR. 
Using the 'Files changed' tab, check that all of the following files were added:

- [ ] The file `packages/{package_name}/{package_name}.tsv` was added to the PR.
- [ ] The file `packages/{package_name}/{package_name}.tsv_patch.sh` was added
      to the PR from template.
- [ ] The file `packages/{package_name}/script_versions.txt` was added to the
      PR.
- [ ] The file `packages/{package_name}/{package_name}.config` was added to the
    PR from template.
<!-- TODO: Follow the steps outlined above and tick them off as you go. -->

### Additional configuration

Additional configuration may be required when processing the data through nf-core/eager.
If you think this may be the case here, please either leave a comment about it in the PR or
add the relevant parameters within the `params` section at the end of the package config file.
For example, if the published data from the paper have internal barcodes, please mention that
in a comment, or provide the relevant nf-core/eager parameters in the `params` section.

<!-- - [ ] I have selected the appropriate config for the CaptureType of the package. -->
- [ ] If any nf-core/eager parameters need to be altered from their defaults, I
      have commented so in this PR (or added the relevant parameters within the 
      `params` section at the end of the package config file).
