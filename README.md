# multicastpy

## Install

```shell
pip install multicastpy
```


## Usage

`multicastpy` provides functionality to turn individual versions of individual corpora of
[Multi-CAST](https://multicast.aspra.uni-bamberg.de/) into [cldfbench](https://github.com/cldf/cldfbench)-curated datasets.

The typical workflow starts with downloading all Multi-CAST data:
```shell
multicast download <repos>
```
where `<repos>` is the name of a local directory.

Based on this data `<repos>`, `cldfbench`-curated repositories can be seeded with the data for a
particular version of a particular corpus:
```shell
multicast cldfbench --corpus <corpus> --version <version> --target-repos <trepos> <repos>
```

To list all available corpora in the data repos, run
```shell
multicast cldfbench <repos> 
```

To list all available versions of a given corpus, run
```shell
multicast cldfbench <repos> --corpus <corpus>
```

The resulting dataset repository can then be curated using `cldfbench`, i.e.
- CLDF can be created via 
  - `cldfbench makecldf --with-zenodo --with-cldfreadme cldfbench_<dsid>.py`
  - `cldfbench readme cldfbench_<dsid>.py`
  - `cldf validate cldf`
  - `cldf splitmedia cldf`
  - `git commit -a -m"..." .`
  - `git tag -a vXXXX -m"..."`
  - `git push origin`
  - `git push origin --tags`
