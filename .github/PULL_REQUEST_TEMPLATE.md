<!--
# poseidon-framework/minotaur-recipes package request

Hello there!

Thanks for suggesting a new publication to add to the Poseidon Minotaur Archive!
Please ensure you are completing all the TODOs outlined in these comments for each section.
-->

Closes #XXX <!-- TODO: Please link the issue requesting the package here. -->

## PR Checklist

- [ ] Add the appropriate label to your PR (`new package` or `package update`).
- [ ] The PR title is in the format `Add/update package: {package_name}`.
- [ ] The PR description includes a link to the issue requesting the package its
      update. (Add to `Closes #XXX` above.)

If adding or updating a package:

- [ ] This PR contains a sequencingSourceFile (`.ssf`) for the requested
      package.
- [ ] The name of the `.ssf` file(s) matches the package name (i.e.
      `packages/2023_my_package/2023_my_package.ssf`).
- [ ] Comment `@delphis-bot create recipe` to this pull request to awaken
      Poseidon's trusty helper. (This should be repeated whenever changes are
      made to the SSF file contents).

Delphis-bot will then add a number of files to the PR. Check that they are all
there:

- [ ] The file `packages/{package_name}/{package_name}.tsv` was added to the PR.
- [ ] The file `packages/{package_name}/{package_name}.tsv_patch.sh` was added
      to the PR from template.
- [ ] The file `packages/{package_name}/script_versions.txt` was added to the
      PR.
- [ ] The file `packages/{package_name}/{package_name}.config` was added to the
    PR from template.
<!-- TODO: Follow the steps outlined above and tick them off as you go. -->

## Human validation

<!-- TODO: Please do the minimal validation of the files outlined below -->

### Package SSF file (`*.ssf`)

- [ ] I confirm that the `poseidon_IDs`, `udg`, and `library_built` are filled
      and correct.
- [ ] I made sure to leave `notes` where necessary to explain any special
      cases/judgement calls made for data entries.

### Package TSV file (`*.tsv`)

- [ ] I confirm that the `UDG`, `Strandedness` columns are correct for each
      library.
- [ ] I confirm that the `R1_target_file` and `R2_target_file` columns point to
      the correct FastQ files for the library (i.e. consistent with SSF file).

### Package config file (`*.config`)

The template config file includes a few `TODO` statements, and information about
them. Please ensure that you:

- [ ] I have selected the appropriate config for the CaptureType of the package.
- [ ] If any nf-core/eager parameters need to be altered from their defaults, I
      have added them within the `params` section at the end of the package
      config file.
