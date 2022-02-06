import subprocess
import datetime
import re


class New_semver:
    """
    A class for updating semantic versions and generating draft release notes.

    Throws error if no tags exist yet.
    Overwrites previous .release-notes.txt
    Breaks if no tags or new commits.

    Requires user actions:
    * merge changes to main first 
    * revision of generated .release-notes.txt
    * approval before commiting version/date updates
    * approval before making release tag

    References:
    * https://semver.org/
    * https://www.conventionalcommits.org/en/v1.0.0/
    * https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines

    Commit format: "feat(scope)!: message"

    * scope is an optional noun
    * add ! only for breaking changes
    * no colons in message content

    Some types:
    * docs (documentation)
    * feat (add/remove feature)
    * fix (bug fix)
    * perf (performance improvement)
    * refactor (change doesn't address bug/feature)
    * style (run formatting: black)
    * test (testing files)

    Scopes point to affected subpackages/modules:
    * (call)

    Semantic versioning:

    Basic scheme in process_git_info():
    * major = "!"
    * minor = "feat"
    * patch = ("docs", "fix", "perf", "refactor", "style")
    """

    def get_git_info(self):

        # Checkout main
        subprocess.call(["git", "checkout", "main"])

        # Get latest tag
        self.version_old = (
            subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
            .decode("utf-8")
            .strip()
        )

        commit_range = self.version_old + "..HEAD"

        # Get commits since last tag
        self.recent_commits = (
            subprocess.check_output(
                [
                    "git",
                    "log",
                    "--no-merges",
                    r"--pretty=format:%s----%ci",
                    commit_range,
                ]
            )
            .decode("utf-8")
            .strip()
        )

    def process_git_info(self):

        # Parse commits
        l = self.recent_commits.split("\n")
        l2 = [[x.split("----")[0], x.split("----")[1]] for x in l]

        # Parse dates
        for x in range(len(l2)):
            dt = l2[x][1].split(" +")[0]
            l2[x][1] = datetime.datetime.fromisoformat(dt)

        # Get activity summary
        commit_types = [x[0].split(": ")[0] for x in l2]
        self.commit_summary = {i: commit_types.count(i) for i in commit_types}

        # Sort commits by type
        commits_sorted = {}
        major = "!"
        minor = "feat"
        patch = ("docs", "fix", "perf", "refactor", "style")
        commits_sorted["Major changes:"] = [x for x in l2 if "!" in x[0]]
        l3 = [x for x in l2 if not "!" in x[0]]
        commits_sorted["Minor changes:"] = [x for x in l3 if x[0].startswith(minor)]
        commits_sorted["Patches:"] = [x for x in l3 if x[0].startswith(patch)]

        self.commits_sorted = commits_sorted

    def update_semver(self):

        # Make proposed new version number
        v_mod = re.search("\D*(\d+\.\d+\.\d+)\D*", self.version_old)
        v_mod = v_mod.group(1)
        v_int = v_mod.split(".")
        v_int = [int(x) for x in v_int]

        if len(self.commits_sorted["Major changes:"]) > 0:
            v_int[0] += 1
            v_int[1] = 0
            v_int[2] = 0
        elif len(self.commits_sorted["Minor changes:"]) > 0:
            v_int[1] += 1
            v_int[2] = 0
        elif len(self.commits_sorted["Patches:"]) > 0:
            v_int[2] += 1

        self.semver_new = ".".join(str(x) for x in v_int)
        self.version_new = "".join(["v", self.semver_new])

    def draft_release_notes(self):

        # Make draft release notes
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        header = "Release notes: " + self.version_new + " (" + now + ")\n\n"
        draft_notes = [header]
        for k, v in self.commits_sorted.items():
            if len(v):
                # draft_notes.append(f"\n{k}\n") # to list changed by type
                for l in v:
                    draft_notes.append("-{}\n".format(l[0].split(":")[1]))

        self.draft_notes = draft_notes

    def save_release_notes(self):

        # To print to draft file
        self.filename = ".release-notes.txt"
        with open(self.filename, "w") as f:
            for line in self.draft_notes:
                f.write(line)

        print("\nFINISHED draft release notes")
        print("\n1. Data processed for commits:", self.commit_summary)
        print("2. Draft stored in", self.filename)

    def replace_old_details(self, file, prefix, suffix, type="semver"):
        """Update semver/date in file.

        Where prefix/suffix are line characters surrounding detail.
        """

        # Get file and line with detail
        with open(file, "r") as f:
            data = f.read()
        lines = data.split("\n")

        detail_line = None
        detail_new = None

        # Prep semver input
        if type == "semver":
            detail_line = re.compile(prefix + "(\d+\.\d+\.\d+)" + suffix)
            detail_new = self.release_version

        # Prep date input
        elif type == "date":
            if file.endswith(".cff"):
                detail_new = datetime.datetime.now().strftime("%Y-%m-%d")
                detail_line = re.compile(prefix + "(\d\d\d\d-\d\d-\d\d)" + suffix)
            else:
                print("ERROR setting date format")
        else:
            print("ERROR detail line")

        # Find old detail
        found = list(filter(detail_line.match, lines))
        if len(found) != 1:
            print("WARNING no/several details found", found)
        else:
            found = found[0]
        print("\nold detail line:", found)
        index = lines.index(found)

        # Replace old detail
        lines[index] = prefix + detail_new + suffix
        print("new detail line:", lines[index])

        # Prepare for save
        lines = [x + "\n" for x in lines]
        if lines[-1] in ["", "\n"]:
            del lines[-1]

        # Overwrite file
        with open(file, "w") as f:
            for line in lines:
                f.write(line)

        print("\n1. Check new detail in file")

    def make_release(self):

        # Ask for input before making release
        _ = input(
            "\nRevise \".release-notes.txt\" & press any key to continue"
        )

        # Get approved release version
        file = ".release-notes.txt"
        with open(file, "r") as f:
            data = f.read()
        lines = data.split("\n")

        release_version = re.search(".*v(\d+\.\d+\.\d+).*", lines[0])

        if release_version:
            self.release_version = release_version.group(1)
            print("release version = ", self.release_version)
        else:
            print("ERROR extracting release version from .release-notes.md")

        # Update version numbers in repository
        jobs1 = [
            ["CITATION.cff", "version: ", ""],
            ["setup.cfg", "version = ", ""],
        ]
        for job in jobs1:
            self.replace_old_details(file=job[0], prefix=job[1], suffix=job[2])

        # Update dates in repository
        jobs2 = [
            ["CITATION.cff", "date-released: ", ""],
        ]
        for job in jobs2:
            self.replace_old_details(
                file=job[0], prefix=job[1], suffix=job[2], type="date"
            )

        do_commit = input("\nCommit changed files to main? y/n")

        # Commit version/date updates
        if do_commit == "y":
            subprocess.call(["git", "add", "CITATION.cff", "setup.cfg"])
            subprocess.call(["git", "commit", "-m", "docs: update"])

        do_tag = input("\nCreate new release tag? y/n")

        # Make release
        if do_tag == "y":
            subprocess.call(
                ["git", "tag", self.version_new, "-a", "--file", self.filename]
            )

            # Finish
            print("\nDONE: to view changes, run   git show", self.version_new)

    def __repr__(self) -> str:
        return ""

    def __init__(self):
        self.get_git_info()
        self.process_git_info()
        self.update_semver()
        self.draft_release_notes()
        self.save_release_notes()
        self.make_release()

if __name__ == '__main__':
    New_semver()