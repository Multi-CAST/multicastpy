
Releasing multicastpy
=====================

- Do platform test via tox:
  ```shell
  tox -r
  ```

- Make sure statement coverage >= 99%
- Make sure flake8 passes:
  ```shell
  flake8 src
  ```

- Update the version number, by removing the trailing `.dev0` in:
  - `setup.cfg`

- Create the release commit:
  ```shell
  git commit -a -m "release <VERSION>"
  ```

- Create a release tag:
  ```shell
  git tag -a v<VERSION> -m"<VERSION> release"
  ```

- Push to github:
  ```shell
  git push origin
  git push --tags
  ```
