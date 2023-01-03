import requests
import git
import os
import re
import shutil
import sys

def main():
    user_name = sys.argv[1]
    year = sys.argv[2]
    bot_user = sys.argv[3]
    bot_email = sys.argv[4]
    repos = requests.get(f"https://api.github.com/users/{user_name}/repos?per_page=100").json()
    for repo in repos:
        if repo["fork"]:
            continue
        if f"{year}-" not in repo["pushed_at"]:
            continue
        git_repo = git.Repo.clone_from(repo["html_url"], repo["name"])
        git_repo.config_writer().set_value("user", "name", bot_user).release()
        git_repo.config_writer().set_value("user", "email", bot_email).release()
        license_file_path = os.path.join(repo["name"], "LICENSE")
        if not os.path.isfile(license_file_path):
            continue
        license_text = open(license_file_path, "r").readlines()
        updated = False
        for idx, line in enumerate(license_text):
            r = re.match(r"Copyright \(c\) (\d{4})-?(\d{4})? (.*)", line.strip())
            if r is not None:
                old_year = r.group(1)
                new_year = year
                if len(r.groups()) == 2:
                    rest = r.group(2)
                else:
                    rest = r.group(3)
                license_text[idx] = updated_text = f"Copyright (c) {old_year}-{new_year} {rest}\n"
                updated = (license_text[idx] == updated_text)
                break
        if not updated:
            os.rmdir(repo["name"])
        with open(license_file_path, "w") as f:
            for line in license_text:
                f.write(line)
        git_branch_name = f"automation/license_{year}_update"
        git_repo.index.add("LICENSE")
        git_repo.git.checkout("-b", git_branch_name)
        git_repo.index.commit(f"Update LICENSE for {year} year")
        git_repo.git.push("--set-upstream", "origin", git_branch_name)
        shutil.rmtree(repo["name"])

if __name__ == "__main__":
    main()
