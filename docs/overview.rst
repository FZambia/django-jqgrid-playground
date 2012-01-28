.. _overview:

What is Django jQuery Grid Admin?
=================================
First of all - it's Django application. 

All django users know that this framework goes with perfect administration 
page included. It has some useful javascript widgets and pretty interface. But what if we try to speed up its performance 
using ajax technology and implove usability adding some popular javascript widgets such as TinyMCE, Chosen, Datepickers and
Multiselects. It could be nice, couldn't it? 

So, Django jQuery Grid Admin app is all about it. Built on the top of jQuery UI, it 
uses jQuery Grid plugin to display model's data and jQuery UI Dialog widget to edit model's instances.

How does it look like?
======================
Oh, yes, the most interesting question!

Just take a look at some screenshots:
------------------------------------
* http://postimage.org/image/7r904g8sh/
* http://postimage.org/image/a1tqmrwd1/
* http://postimage.org/image/4hh9c4xhx/

Try a demonstration
--------------------
* http://wellspring.ru/jsadmin/

Watch this video
-----------------
* 

Let's Get It Started
====================
Current version of this app is not available on PyPi.

Some installation steps
------------------------

1. First, you need to clone this repository on Github: https://github.com/FZambia/Django-jQuery-Grid-Admin

2. Then place 'djgrid' folder in your project root and add 'djgrid' in `INSTALLED_APPS`

3. In your project you definetely have base template, i suggest 'base.html'. Grid Admin inherits it in '`templates/djgrid/djgrid_base.html`' file. All you need to do is to define proper block tag names

4. Copy 'js' folder to your project's media folder 

5. The last step. In your `urls.py` you need to write some classes that is a grid admin instances ::

	from djgrid.resources import GridResource
	class Resource(GridResource):
	    class Meta:
	        register = [['auth','user']]
	resource = Resource()

In urlpatterns add th following line: ::

	(r'^',include(resource.urls)),

**And finally** go to `http://yourproject.com/djgrid/` and you will see django's User model admin grid page
