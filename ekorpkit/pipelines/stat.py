import time
from pathlib import Path
from ekorpkit import eKonf
from ekorpkit.utils.func import humanbytes, get_modified_time
from ekorpkit.pipelines.pipe import apply
from ekorpkit.utils.func import elapsed_timer
from wasabi import msg


class SummaryInfo:
    def __init__(self, **args):
        self.args = eKonf.to_dict(args)
        self.name = self.args["name"]
        self.stat_args = self.args.get("stats", None)
        self.data_dir = self.args.get("data_dir", None)
        self.verbose = self.args.get("verbose", False)
        self.info_path = Path(self.data_dir) / self.args.get(
            "info_file", f"info-{self.name}.yaml"
        )
        self.info_list = self.args.get("info_list", [])
        self.stat_before_processing = self.args.get("stat_before_processing", None)
        self.update_files_info = self.args.get("update_files_info", {})
        self.aggregate_info = self.args.get("aggregate_info", {})
        self.modified_info = self.args.get("modified_info", {})

        self.info = {}
        self.stats = {}
        self.splits = {}

    def load(self, info={}):
        if self.info_path.exists():
            self.info = eKonf.to_dict(eKonf.load(self.info_path))
        else:
            self.info = {}

        for key in self.info_list:
            if info.get(key) is not None:
                self.info[key] = info[key]

        if "stats" in self.info:
            self.stats = self.info["stats"]
        if "splits" in self.info:
            self.splits = self.info["splits"]

        if self.verbose:
            msg.good(f"Loading info file: {self.info_path}")
            eKonf.pprint(self.info)

    def init_stats(self, df=None, split_name=None, stats={}):
        if self.verbose:
            msg.good(f"Initializing statistics for split: {split_name}")
        if split_name:
            stats["name"] = split_name

        stat_args = self.stat_before_processing
        if stat_args is not None:
            with elapsed_timer(format_time=True) as elapsed:
                for k, v in self.stat_args.items():
                    if k not in stat_args:
                        stat_args[k] = v

                stat_fn = eKonf.instantiate(stat_args)
                stats = stat_fn(df)
                # stats = summary_stats(df, **stat_args)
                msg.good(
                    f" >> elapsed time to calculate statistics before processing: {elapsed()}"
                )
            stats.update(stats)

        if split_name:
            self.splits[split_name].update(stats)
        else:
            self.stats.update(stats)

    def calculate_stats(self, df, split_name=None):
        if self.verbose:
            msg.good(f"Calculating statistics for split: {split_name}")
        if split_name and split_name not in self.splits:
            self.init_stats(df, split_name)
        with elapsed_timer(format_time=True) as elapsed:
            stat_fn = eKonf.instantiate(self.stat_args)
            stats = stat_fn(df)
            msg.good(f" >> elapsed time to calculate statistics: {elapsed()}")

        if split_name:
            self.splits[split_name].update(stats)
        else:
            self.stats.update(stats)

    def _update_info(self):
        if self.stats:
            if "stats" not in self.info:
                self.info["stats"] = {}
            self.info["stats"].update(self.stats)
        else:
            if "stats" in self.info and not self.info["stats"]:
                del self.info["stats"]

        if self.splits:
            if "splits" not in self.info:
                self.info["splits"] = {}
            self.info["splits"].update(self.splits)

            files_info = {key: {} for key in self.update_files_info}
            for i, (split_name, split_info) in enumerate(self.splits.items()):
                for key, val in self.update_files_info.items():
                    if val in split_info:
                        files_info[key][split_name] = split_info[val]
                for key, val in self.aggregate_info.items():
                    if val in split_info:
                        if i == 0:
                            self.info[key] = split_info[val]
                        else:
                            self.info[key] += split_info[val]
            self.info["size_in_human_bytes"] = humanbytes(self.info["size_in_bytes"])

            for key in self.update_files_info:
                self.info[key] = files_info[key]

            for key, value in self.modified_info.items():
                vals = [
                    get_modified_time(f"{self.data_dir}/{split[value]}")
                    for split in self.info["splits"].values()
                    if value in split
                ]
                vals = [v for v in vals if v is not None]
                if vals:
                    self.info[key] = max(vals)
        else:
            if "splits" in self.info and not self.info["splits"]:
                del self.info["splits"]

        self.info["info_updated"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    def save(self):
        self._update_info()

        eKonf.save(self.info, f=self.info_path)
        if self.verbose:
            msg.good(f"Saving updated info file: {self.info_path}")
            eKonf.pprint(self.info)


def summary_stats(
    df,
    **args,
):

    args = eKonf.to_dict(args)
    key_columns = args.get("key_columns", None)
    num_columns = args.get("num_columns", None)
    agg_funcs = args.get("agg_funcs", None)
    rename_columns = args.get("rename_columns", None)
    convert_to_humanbytes = args.get("convert_to_humanbytes", None)
    num_workers = args.get("num_workers", None)
    method = args.get("method", None)

    df = df.copy(deep=True)
    num_workers = num_workers if num_workers else 1
    text_keys = key_columns["text"]
    if isinstance(text_keys, list):
        for col in text_keys:
            df[col].fillna("", inplace=True)
            df[col] = df[col].astype(str)
        separator = "\n\n"
        text_key = text_keys[0]
        df[text_key] = df[text_keys].agg(separator.join, axis=1)
    else:
        text_key = text_keys
        df[text_key] = df[text_key].astype(str)

    for col, func in num_columns.items():
        len_func = eKonf.instantiate(method[func])
        df[col] = apply(len_func, df[text_key], description=f"apply {func} to {col}")

    agg_funcs = {k: list(v) for k, v in agg_funcs.items()}
    df_sum = df.groupby(lambda _: True).agg(agg_funcs)
    df_sum.columns = ["_".join(x) for x in df_sum.columns.values]
    df_sum.rename(columns=dict(rename_columns), inplace=True)
    info = df_sum.to_dict(orient="records")[0]
    if convert_to_humanbytes:
        for k, v in convert_to_humanbytes.items():
            if k in info:
                info[v] = humanbytes(info[k])
    return info
