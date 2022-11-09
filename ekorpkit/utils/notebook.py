import logging
import os
import sys
from ekorpkit.io.file import read


logger = logging.getLogger(__name__)


def _is_notebook():
    try:
        get_ipython
    except NameError:
        return False
    shell_type = get_ipython().__class__.__name__
    # logger.info(f"shell type: {shell_type}")
    if shell_type == "ZMQInteractiveShell":
        return True  # Jupyter notebook or qtconsole
    elif shell_type == "Shell":
        return True  # Google colab
    elif shell_type == "TerminalInteractiveShell":
        return False  # Terminal running IPython
    else:
        return False  # Other type


def _is_colab():
    is_colab = "google.colab" in sys.modules
    if is_colab:
        logger.info("Google Colab detected.")
    else:
        logger.info("Google Colab not detected.")
    return is_colab


def _get_display():
    try:
        from ipywidgets import Output
    except ImportError:
        logger.info("ipywidgets not installed.")
        return None

    if _is_notebook():
        return Output()
    else:
        return None


def _clear_output(wait=False):
    from IPython import display

    if _is_notebook():
        display.clear_output(wait=True)


def _display(
    *objs,
    include=None,
    exclude=None,
    metadata=None,
    transient=None,
    display_id=None,
    raw=False,
    clear=False,
    **kwargs,
):
    from IPython import display

    if _is_notebook() and objs is not None:
        return display.display(
            *objs,
            include=include,
            exclude=exclude,
            metadata=metadata,
            transient=transient,
            display_id=display_id,
            raw=raw,
            clear=clear,
            **kwargs,
        )


def _display_image(
    data=None,
    url=None,
    filename=None,
    format=None,
    embed=None,
    width=None,
    height=None,
    retina=False,
    unconfined=False,
    metadata=None,
    **kwargs,
):
    from IPython import display

    if _is_notebook():
        img = display.Image(
            data=data,
            url=url,
            filename=filename,
            format=format,
            embed=embed,
            width=width,
            height=height,
            retina=retina,
            unconfined=unconfined,
            metadata=metadata,
            **kwargs,
        )
        return display.display(img)


def _hide_code_in_slideshow():
    from IPython import display
    import binascii

    uid = binascii.hexlify(os.urandom(8)).decode()
    html = """<div id="%s"></div>
    <script type="text/javascript">
        $(function(){
            var p = $("#%s");
            if (p.length==0) return;
            while (!p.hasClass("cell")) {
                p=p.parent();
                if (p.prop("tagName") =="body") return;
            }
            var cell = p;
            cell.find(".input").addClass("hide-in-slideshow")
        });
    </script>""" % (
        uid,
        uid,
    )
    display.display_html(html, raw=True)


def colored_str(s, color="black"):
    # return "<text style=color:{}>{}</text>".format(color, s)
    return "<text style=color:{}>{}</text>".format(color, s.replace("\n", "<br>"))


def _cprint(str_tuples):
    from IPython.display import HTML as html_print
    from IPython.display import display

    display(html_print(" ".join([colored_str(ti, color=ci) for ti, ci in str_tuples])))


def _create_dropdown(
    options,
    value,
    description,
    disabled=False,
    style={"description_width": "initial"},
    layout=None,
    **kwargs,
):
    import ipywidgets as widgets

    layout = (
        widgets.Layout(width="auto") if layout is None else widgets.Layout(**layout)
    )
    dropdown = widgets.Dropdown(
        options=options,
        value=value,
        description=description,
        disabled=disabled,
        style=style,
        layout=layout,
        **kwargs,
    )
    return dropdown


def _create_textarea(
    value,
    description,
    placeholder="",
    disabled=False,
    style={"description_width": "initial"},
    layout=None,
    **kwargs,
):
    import ipywidgets as widgets

    layout = (
        widgets.Layout(width="auto") if layout is None else widgets.Layout(**layout)
    )
    textarea = widgets.Textarea(
        value=value,
        placeholder=placeholder,
        description=description,
        disabled=disabled,
        style=style,
        layout=layout,
        **kwargs,
    )
    return textarea


def _create_button(description, button_style="", icon="check", layout=None, **kwargs):
    import ipywidgets as widgets

    layout = (
        widgets.Layout(width="auto") if layout is None else widgets.Layout(**layout)
    )
    button = widgets.Button(
        description=description,
        button_style=button_style,
        icon=icon,
        layout=layout,
        **kwargs,
    )
    return button


def _create_radiobutton(
    options,
    description,
    value=None,
    disabled=False,
    style={"description_width": "initial"},
    layout=None,
    **kwargs,
):
    import ipywidgets as widgets

    layout = (
        widgets.Layout(width="auto") if layout is None else widgets.Layout(**layout)
    )
    radiobutton = widgets.RadioButtons(
        options=options,
        value=value,
        description=description,
        disabled=disabled,
        style=style,
        layout=layout,
        **kwargs,
    )
    return radiobutton


def _create_image(
    filename=None,
    format=None,
    width=None,
    height=None,
    **kwargs,
):
    import ipywidgets as widgets

    # from urllib.request import urlopen

    if filename is None:
        url = "https://github.com/entelecheia/ekorpkit-book/raw/main/assets/figs/placeholder.png"
        # img = urlopen(url).read()
        img = read(url)
        format = "png"
    else:
        img = read(filename)
        format = format or filename.split(".")[-1]
    image = widgets.Image(
        value=img,
        format=format,
        width=width,
        height=height,
        **kwargs,
    )
    return image


def _create_floatslider(
    min=0.0,
    max=1.0,
    step=0.1,
    value=None,
    description="",
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format=".1f",
    style={"description_width": "initial"},
    layout=None,
    **kwargs,
):
    import ipywidgets as widgets

    layout = (
        widgets.Layout(width="auto") if layout is None else widgets.Layout(**layout)
    )
    slider = widgets.FloatSlider(
        min=min,
        max=max,
        step=step,
        value=value,
        description=description,
        disabled=disabled,
        continuous_update=continuous_update,
        orientation=orientation,
        readout=readout,
        readout_format=readout_format,
        style=style,
        layout=layout,
        **kwargs,
    )
    return slider
