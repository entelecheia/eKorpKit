import numpy as np
import copy
import matplotlib.pyplot as plt
import seaborn as sns
from cmath import isinf
from pathlib import Path
from .base import set_style, set_figure
from ekorpkit import eKonf


def plot(data, verbose=False, **kwargs):
    kwargs = eKonf.to_dict(kwargs)
    plots = kwargs.get("plots")
    figures = kwargs.get("figures")
    series = {} or kwargs.get("series")
    plot = {} or kwargs.get("plot")
    subplots = {} or kwargs.get("subplots")
    figure = {} or kwargs.get("figure")
    savefig = {} or kwargs.get("savefig")

    if data is None:
        if verbose:
            print("No data to plot")
        return

    set_style(**plot)
    figsize = plot.get("figsize", None)
    if figsize is not None and isinstance(figsize, str):
        figsize = eval(figsize)

    dataform = series.get("form", "individual")
    xcol = series["x"]
    if isinstance(xcol, list):
        xcol = xcol[0]
    x = data[xcol] if xcol in data.columns else data.index
    ycols = series["y"]
    if isinstance(ycols, str):
        ycols = [ycols]

    if subplots["nrows"] > 1 or subplots["ncols"] > 1:
        fig, axes = plt.subplots(**subplots, figsize=figsize)
        ax = None
        sencondary_axes = {}
        axes = axes.flatten()
    else:
        plt.figure(figsize=figsize, tight_layout=True)
        ax = plt.gca()
        axes = [ax]

    if dataform == "individual":
        if isinstance(plots, dict):
            plots = [plots]
        for _plot_cfg_ in plots:
            _func_ = eval(_plot_cfg_.get(eKonf.Keys.FUNCTION))
            y = _plot_cfg_.pop("y")
            secondary_y = _plot_cfg_.get("secondary_y", False)
            if secondary_y:
                secondary_to = _plot_cfg_.get("secondary_to", 0)
                if verbose:
                    print(f"Creating secondary axis to axis[{secondary_to}]")
                if secondary_to in sencondary_axes:
                    ax = sencondary_axes[secondary_to]
                else:
                    ax = axes[secondary_to].twinx()
                    sencondary_axes[secondary_to] = ax
            else:
                axno = _plot_cfg_.get("axno", 0)
                ax = axes[axno]
            _func_(ax, x, y, data, **_plot_cfg_)
    else:
        if isinstance(plots, list):
            _plot_cfg_ = plots[0]
        else:
            _plot_cfg_ = plots
        _func_ = eval(_plot_cfg_.get(eKonf.Keys.FUNCTION))
        if len(ycols) == 1:
            ycols = ycols[0]
        y = _plot_cfg_.pop("y")
        if _plot_cfg_.get("dataform"):
            dataform = _plot_cfg_.pop("dataform")
        if dataform == "wide":
            if xcol and xcol in data.columns:
                _data = data.set_index(xcol)[ycols]
            else:
                _data = data[ycols]
            _func_(ax, x=None, y=None, data=_data, **_plot_cfg_)
        else:
            _func_(ax, x=xcol, y=ycols, data=data, **_plot_cfg_)

    if isinstance(figures, dict):
        figures = [figures]
    for _fig_cfg_ in figures:
        secondary_y = _fig_cfg_.get("secondary_y", False)
        if secondary_y:
            secondary_to = _fig_cfg_.get("secondary_to", 0)
            if secondary_to in sencondary_axes:
                ax = sencondary_axes[secondary_to]
            else:
                ax = None
        else:
            axno = _fig_cfg_.get("axno", 0)
            ax = axes[axno]
        add_decorations(ax, **_fig_cfg_)
        set_figure(ax, **_fig_cfg_)

    fname = savefig.get("fname", None)
    if fname:
        Path(fname).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(**savefig)
        if verbose:
            print(f"Saved figure to {fname}")


def lineplot(ax=None, x=None, y=None, data=None, **kwargs):
    _parms_ = {} or kwargs.get(eKonf.Keys.PARMS)
    if ax is None:
        ax = plt.gca()
    sns.lineplot(x=x, y=y, data=data, ax=ax, **_parms_)


def stackplot(ax=None, x=None, y=None, data=None, **kwargs):
    _parms_ = {} or kwargs.get(eKonf.Keys.PARMS)
    if ax is None:
        ax = plt.gca()
    if x is None:
        x = data.index
    elif isinstance(x, str):
        x = data[x]
    plt.stackplot(x, data[y].T, **_parms_)


def scatter(ax=None, x=None, y=None, data=None, **kwargs):
    _parms_ = {} or kwargs.get(eKonf.Keys.PARMS)
    if ax is None:
        ax = plt.gca()
    sns.scatterplot(x=x, y=y, data=data, ax=ax, **_parms_)


def add_decorations(ax=None, **kwargs):
    if ax is None:
        ax = plt.gca()
    axvspans = [] or kwargs.get("axvspans")
    annotations = [] or kwargs.get("annotations")

    if isinstance(axvspans, dict):
        axvspans = [axvspans]
    if isinstance(annotations, dict):
        annotations = [annotations]

    for span in axvspans:
        if isinstance(span, dict):
            ax.axvspan(**span)
    for annot in annotations:
        if isinstance(annot, dict):
            if annot.get("xy") is not None and isinstance(annot.get("xy"), str):
                annot["xy"] = eval(annot["xy"])
            if annot.get("xytext") is not None and isinstance(annot.get("xytext"), str):
                annot["xytext"] = eval(annot["xytext"])
            ax.annotate(**annot)


def treemap(
    df,
    fig_filepath,
    scale=1.5,
    columns=None,
    treemap=None,
    layout=None,
    update_layout=None,
    **kwargs,
):
    # textinfo = "label+value+percent parent+percent root"
    # import plotly.express as px
    import plotly.graph_objects as go

    labels = list(df[columns.label].to_list())
    values = list(df[columns.value].to_list())
    parents = list(df[columns.parent].to_list())

    layout = go.Layout(**layout)
    fig = go.Figure(
        go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            **treemap,
        ),
        layout=layout,
    )
    fig.update_layout(
        **update_layout,
    )

    fig.write_image(fig_filepath, scale=scale)


def barplot(df, columns=None, savefig={}, plot={}, figure={}, verbose=False, **kwargs):
    if df is None:
        if verbose:
            print("No data to plot")
        return
    set_style(**plot)
    figsize = plot.get("figsize", None)
    if figsize is not None and isinstance(figsize, str):
        figsize = eval(figsize)
    ycols = columns.yvalue
    xcol = columns.xvalue
    index = columns.get("index", None)
    if index:
        df.index = list(index)
        xcol = None
    data = df

    # plt.figure(figsize=figsize, tight_layout=True)
    stacked = plot.get("stacked", False)
    ax = data.plot(x=xcol, y=ycols, kind="bar", stacked=stacked, figsize=figsize)
    set_figure(ax, **figure)
    plt.tight_layout()

    fname = savefig.get("fname", None)
    if fname:
        Path(fname).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(**savefig)
        if verbose:
            print(f"Saved figure to {fname}")
