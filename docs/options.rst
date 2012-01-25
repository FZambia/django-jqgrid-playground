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

Description directives
----------------------
* **fields** - list of fields for model to display on grid (if omitted then we use all model fields)

* **exclude** -  list of excluded fields for model (if omitted then we do not exclude any field)

* **plugins** - list of fields for which you want to use widget/plugin or magic word 'ALL' (if omitted then we do not use any plugin)

* **safe** - list of fields for which you do not want to escape html (if omitted then we escape all column values)

Example with all options overrided
-----------------------------------
In this code snippet we override all available options to customize behaviour of grid admin: ::

    from djgrid.resources import GridResource
    
    class Resource(GridResource):
        class Meta:
            register = [['blog','post'],['blog','comment'],['auth','user']]
            description = {
                'post':{
                    'fields':['title','teaser','author','published_at','updated_at'],
                    'plugins':'ALL',
                    'safe':['author']
                },
                'comment':{
                
                },
                'user': {
                    'exclude': ['password'],
                    'plugins': ['permissions','groups']
                }
            }
            prefix = 'custom_admin'
            readonly = False
            inline = True
            datetime_format = "%d/%m/%Y %H-%M"
            date_format = "%d/%m/%Y"
            time_format = "%H-%M"
            grid_rownum = 30
            datepicker_format = "dd/mm/yy"
            timepicker_format = "hh-mm"
            dialog_width = '60%'
            dialog_max_height = 400
            wysiwyg_height = 200
            save_on_top = True
            navigation = False

Next you need to create instance of Resource and add resource's urls in urlpatterns: ::

    resource = Resource()
    urlpatterns = patterns('',
        url(r'^$', include(resource.urls)),
    )

