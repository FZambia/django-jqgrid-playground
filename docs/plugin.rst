.. _plugin:

Current javascript plugin support
=================================
Django jQuery Grid Admin uses javascript plugins to display different 
model fields. By default, the all unused. You can turn on widget on fields you
want or you can turn on all widjets for a model.

Plugin list:
-----------

* **TinyMCE** for textareas (http://www.tinymce.com/)
* **Chosen** for selects (http://harvesthq.github.com/chosen/)
* **jQuery UI datepicker widget** for datefields (http://jqueryui.com/demos/datepicker/)
* **jQuery UI datetimepicker addon** for datetime and time fields (http://trentrichardson.com/examples/timepicker/)
* **jQuery UI MultiSelect Widget by Eric Hynds** for multiple selects (http://erichynds.com/jquery/jquery-ui-multiselect-widget/)

Turn on plugin for field
------------------------

There is 2 ways to turn on plugins:

* list desired field list in `description[model_name]['plugins']`, for example: ::

    class Resource(GridResource):
        class Meta:
            register = [['auth','user'],]
            description = {
                'user':{
                    'plugins':['date_joined','last_login'],
                }
            }
	
* write magic word 'ALL' in plugin section - this will turn on plugin support for all model fields: ::

    class Resource(GridResource):
        class Meta:
            register = [['auth','user'],]
            description = {
                'user':{
                    'plugins':'ALL',
                }
            }

Notice ::

	Unfortunately, second method does not work with many-to-many now, you need to use first method to turn on plugins for them