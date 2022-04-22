import pandas as pd
from wasabi import msg
from ekorpkit import eKonf
from ekorpkit.utils.func import elapsed_timer
from .dataset import Dataset


class Datasets:
    def __init__(self, **args):
        args = eKonf.to_dict(args)
        self.args = args
        self.names = args.get("name")
        if isinstance(self.names, str):
            self.names = [self.names]
        self.verbose = args.get("verbose", False)
        self.data_dir = args["data_dir"]
        self._data_files = self.args.get("data_files", None)
        self._autorun_list = self.args.get("autorun", None)
        use_name_as_subdir = args.get("use_name_as_subdir", True)

        self.column_info = self.args.get("column_info", {})
        self.split_info = self.args.get("splits")
        self.datasets = {}

        self._id_key = "id"
        self._id_separator = "_"
        self._dataset_key = "dataset"
        self._keys = self.column_info.get("keys", None)
        self._id_keys = self._keys[self._id_key]
        if isinstance(self._id_keys, str):
            self._id_keys = [self._id_keys]
        self._data_keys = self.column_info.get("data", None)

        with elapsed_timer(format_time=True) as elapsed:
            for name in self.names:
                print(f"processing {name}")
                args["name"] = name
                args["data_dir"] = self.data_dir
                args["use_name_as_subdir"] = use_name_as_subdir
                if self._data_files is not None:
                    if name in self._data_files:
                        args["data_files"] = self._data_files[name]
                    elif "train" in self._data_files:
                        args["data_files"] = self._data_files
                dataset = Dataset(**args)
                self.datasets[name] = dataset
                if self.split_info is None:
                    self.split_info = list(dataset.splits.keys())
            print(f"\n >>> Elapsed time: {elapsed()} <<< ")

        self._autorun()

    def _autorun(self):
        if isinstance(self._autorun_list, list):
            for _run in self._autorun_list:
                if isinstance(_run, str):
                    getattr(self, _run)()
                elif isinstance(_run, dict):
                    _run = eKonf.to_dict(_run)
                    getattr(self, _run["name"])(**_run["args"])

    def __str__(self):
        classname = self.__class__.__name__
        s = f"{classname}\n----------\n"
        for name in self.datasets.keys():
            s += f"{str(name)}\n"
        return s

    def __getitem__(self, name):
        if name not in self.datasets:
            raise KeyError(f"{name} not in datasets")
        return self.datasets[name]

    @property
    def ID(self):
        return self._id_key

    @property
    def IDs(self):
        return self._id_keys

    @property
    def DATA(self):
        if self._data_keys is None:
            return None
        return list(self._data_keys.keys())

    def load(self):
        for _name in self.datasets:
            self.datasets[_name].load()
        self._loaded = True

    def concatenate(self, append_dataset_name=True):
        self.concat_datasets(append_dataset_name=append_dataset_name)

    def concat_datasets(self, append_dataset_name=True):
        self.splits = {}

        if append_dataset_name:
            if self._dataset_key not in self._id_keys:
                self._id_keys.append(self._dataset_key)

        for split in self.split_info:
            dfs = []
            for name in self.datasets:
                df = self.datasets[name][split]
                if self.DATA:
                    df = df[self.DATA]
                if append_dataset_name:
                    df[self._dataset_key] = name
                dfs.append(df)
            self.splits[split] = pd.concat(dfs, ignore_index=True)
        if self.verbose:
            msg.good(f"concatenated {len(self.datasets)} datasets")
