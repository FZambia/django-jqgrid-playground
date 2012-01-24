.. _plugin:

Available options
=================================
Inspired by django-tastypie (http://django-tastypie.readthedocs.org/en/latest/index.html), Django jQuery Grid Admin
uses similiar resource definition. To enable grid admin you should inherit GridResource class, located in
`resources.py` file. You can override default options in `class Meta`

Required options
----------------

* **register** - this is a list of [app label, model name] you want to add in grid admin. If you want one of your models to display in grid admin - just include it in this list. See example below.

Custom options
--------------
* **prefix** - because you can define several grid resources this option is for different urls to them.

* **description** - one of the most important options. It allows you to define fields for model, to exclude fields of model,to turn on plugin support, to choose fields with "safe" unescaped html.

* **readonly** - if set to `True` then grid will be without edit and delete actions column (DEFAULT `FALSE`)

* **inline** if set to `False` then grid will be without inline editing (DEFAULT `True`)

* **datetime_format** - string that defines datetime format (DEFAULT `"%d.%m.%Y %H:%M"`)

* **date_format** - string that defines date format (DEFAULT `"%d.%m.%Y"`)

* **time_format** - string that defines time format (DEFAULT `"%H:%M"`)

* **grid_rownum** - jQuery Grid number of rows (DEFAULT `20`)

* **datepicker_format** -  jQuery UI date format (DEFAULT `"dd.mm.yy"`)

* **timepicker_format** -  jQuery UI datetimepicker time format (DEFAULT `"hh:mm"`)

* **dialog_width** -  jQuery UI dialog width (DEFAULT `'70%'`)

* **dialog_max_height** -  jQuery UI dialog max height (DEFAULT `500`)

* **wysiwyg_height** -  height of textareas (DEFAULT `400`)

* **save_on_top** -  display `Save` button on top of dialog (DEFAULT `False`)

* **navigation** - show navigation tabs (DEFAULT `True`)


Example with all options overrided
-----------------------------------
not available yet
