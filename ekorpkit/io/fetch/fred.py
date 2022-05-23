from fileinput import filename
import logging
import logging
import os
import pandas as pd
from ekorpkit import eKonf
from ekorpkit.io.file import save_dataframe, load_dataframe

log = logging.getLogger(__name__)


class Fred:
    def __init__(self, **args):
        from fredapi import Fred

        self.args = eKonf.to_dict(args)
        self.autoload = self.args.get("autoload", True)
        self.name = self.args.get("name")
        self.api_key = self.args.get("api_key")
        self.verbose = self.args.get("verbose", True)
        self.series_id = self.args.get("series_id")
        if isinstance(self.series_id, str):
            self.series_id = [self.series_id]
        elif not isinstance(self.series_id, list):
            self.series_id = []
        self.series_name = self.args.get("series_name")
        self.value_column = self.args.get("value_column", "value")
        self.start_date = self.args.get("start_date")
        self.end_date = self.args.get("end_date")
        self.eval_columns = self.args.get("pipeline").get("eval_columns")

        self.output_dir = self.args["output_dir"]
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = self.args["output_file"]
        self.force_download = self.args["force_download"]

        self.fred = Fred(api_key=self.api_key)
        self.data = None

        if self.autoload:
            self.load()

    def get_series(self, series_id, start_date=None, end_date=None, **kwargs):
        """
        Get data for a Fred series id. This fetches the latest known data, and is equivalent to get_series_latest_release()

        Parameters
        ----------
        series_id : str
            Fred series id such as 'CPIAUCSL'
        start_date : datetime or datetime-like str such as '7/1/2014', optional
            earliest observation date
        end_date : datetime or datetime-like str such as '7/1/2014', optional
            latest observation date
        kwargs : additional parameters
            Any additional parameters supported by FRED. You can see https://api.stlouisfed.org/docs/fred/series_observations.html for the full list

        Returns
        -------
        data : Series
            a Series where each index is the observation date and the value is the data for the Fred series
        """
        return self.fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
            **kwargs,
        )

    def load(
        self,
        series_id=None,
        series_name=None,
        start_date=None,
        end_date=None,
        filename=None,
    ):
        if isinstance(series_id, str):
            series_id = [series_id]
        elif not isinstance(series_id, list):
            series_id = []

        if series_name is None:
            if not series_id and self.series_name:
                series_name = self.series_name
            else:
                series_name = "_".join(self.series_id)
        if filename is None:
            filename = f"{series_name}.parquet"
        if not series_id:
            series_id = self.series_id

        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date
        if self.verbose:
            print(f"Loading {series_name}{series_id} from {start_date} to {end_date}")

        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath) or self.force_download:
            self.data = self._load_fred(series_id, series_name, start_date, end_date)
            save_dataframe(self.data, filepath, verbose=self.verbose)
        else:
            log.info(f"{filepath} already exists.")
            self.data = load_dataframe(filepath, verbose=self.verbose)
        return self.data.copy()

    def _load_fred(
        self,
        series_ids=None,
        series_name=None,
        start_date=None,
        end_date=None,
    ):

        _dfs = []
        for series_id in series_ids:
            series = self.fred.get_series(
                series_id=series_id,
                start_date=start_date,
                end_date=end_date,
            )
            df = pd.DataFrame(series, columns=[self.value_column])
            df = eKonf.pipe(self.eval_columns, df)
            if len(series_ids) > 1:
                df["series_id"] = series_id
            df.rename(columns={self.value_column: series_name}, inplace=True)
            if self.verbose:
                print(df.head())
            _dfs.append(df)

        df = pd.concat(_dfs)
        return df
