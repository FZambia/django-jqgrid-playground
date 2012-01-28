# -*- coding: utf-8 -*-
import time as tm
import traceback
from datetime import datetime,date,time

from aed import AED
from grid import Grid

from django import forms
from django.db import models
from django.utils import simplejson
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.db.models import get_model, Sum, Q
from django.core.context_processors import csrf
from django.utils.encoding import smart_unicode
from django.conf.urls.defaults import patterns, url
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404,render_to_response
from django.http import HttpResponse,Http404,HttpResponseRedirect,Http404


"""
MODULE STRUCTURE INSPIRED BY DJANGO-TASTYPIE:
https://github.com/toastdriven/django-tastypie
"""

class GridResourceOptions(object):
    register = []
    description = {}
    readonly = False
    inline = True
    datetime_format = "%d.%m.%Y %H:%M"
    date_format = "%d.%m.%Y"
    time_format = "%H:%M"
    grid_rownum = 20
    datepicker_format = "dd.mm.yy"
    timepicker_format = "hh:mm"
    dialog_width = '70%'
    dialog_max_height = 500
    wysiwyg_height = 400
    save_on_top = False
    navigation = True
    prefix = 'jqgrid-admin'
    
    def __new__(cls, meta=None):
        overrides = {}
        # Handle overrides.
        if meta:
            for override_name in dir(meta):
                # No internals please.
                if not override_name.startswith('_'):
                    overrides[override_name] = getattr(meta, override_name)

        return object.__new__(type('GridResourceOptions', (cls,), overrides))

class DeclarativeMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(DeclarativeMeta, cls).__new__(cls, name, bases, attrs)
        opts = getattr(new_class, 'Meta', None)
        new_class._meta = GridResourceOptions(opts)
        return new_class
        
class GridResource(object):
    __metaclass__ = DeclarativeMeta
    
    UNDEFINED = 'undefined'
    
    ALL = 'all'

    def check(fn):
        def wrapper(cls, request, *args,**kwargs):
            if not request.user.is_superuser:
                return HttpResponseRedirect('/')
            result = fn(cls,request,*args,**kwargs)
            return result
        return wrapper

    @property
    def urls(self):
        """
        Grid Resource urls
        """
        urls = self.base_urls()
        urlpatterns = patterns('',
            *urls
        )
        return urlpatterns

    def base_urls(self):
        """
        The standard URLs this ``Grid Resource`` should respond to.
        """
        return [
            url(r'^(?P<prefix>%s)/(?P<app_label>\w+)/(?P<model_name>\w+)/(?P<object_id>.+)/(?P<action>.+)/$' % self._meta.prefix, self.actionview, name=u"djgrid-actionview"),
            url(r'^(?P<prefix>%s)/(?P<app_label>\w+)/(?P<model_name>\w+)/inline/$' % self._meta.prefix, self.inline, name=u"djgrid-inline"),
            url(r'^(?P<prefix>%s)/(?P<app_label>\w+)/(?P<model_name>\w+)/create/$' % self._meta.prefix, self.actionview, name=u"djgrid-createview"),
            url(r'^(?P<prefix>%s)/(?P<app_label>\w+)/(?P<model_name>\w+)/$' % self._meta.prefix, self.listview, name=u"djgrid-listview"),
            url(r'^(?P<prefix>%s)/$' % self._meta.prefix, self.indexview, name=u"djgrid-indexview"),
        ]
           
    def get_all_model_fields(self, app_label, model_name):
        model = get_model(app_label,model_name)
        fields = [x.name for x in model._meta.fields]
        return fields
    
    def get_field_list(self, app_label = None,model_name = None, model = None):
        """
        returns the list of fields for model to display on grid
        """
        try:
            fields = self._meta.description[model_name]['fields'][:]
        except KeyError,e:
            fields = self.get_all_model_fields(app_label, model_name)
            
        if self._meta.description.has_key(model_name) and 'exclude' in self._meta.description[model_name]:
            for excl in self._meta.description[model_name]['exclude']:
                fields.remove(excl)
                
        return fields
    
    
    def get_plugin_list(self, app_label, model_name):
        """
        return the list of plugins for model
        """
        if self._meta.description.has_key(model_name) and 'plugins' in self._meta.description[model_name]:
            plugins = self._meta.description[model_name]['plugins']
            if isinstance(plugins,str) and plugins.lower()==GridResource.ALL.lower():
                return self.get_all_model_fields(app_label, model_name)
            elif isinstance(plugins,list):
                return plugins
        return []
    
    
    def get_safe_list(self, model_name):
        """
        return the list of fields to use in grid without html escaping
        """
        if self._meta.description.has_key(model_name) and 'safe' in self._meta.description[model_name]:
            return self._meta.description[model_name]['safe']
        return []
    
    def get_field_types(self, fields, model):
        return dict((field, model._meta.get_field(field).__class__.__name__) for field in fields)
        
    def make_custom_field(self, f):
        """
        adds custom parameters to form fields
        """
        formfield = f.formfield()
        if hasattr(formfield,'widget'):
            formfield.widget.attrs.update({'class':formfield.__class__.__name__})
        return formfield
    
    def indexview(self, request, prefix):
        """
        redirects to first model listview
        """
        if not len(self._meta.register):
            return HttpResponse('no registered models')
        app_label = self._meta.register[0][0]
        model_name = self._meta.register[0][1]
        
        return HttpResponseRedirect(reverse('djgrid-listview', kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name}))
    
    @check
    def listview(self, request, prefix, app_label, model_name, **kwargs):
        """
        displays jquery grid with model data
        """
        if [app_label,model_name] not in self._meta.register:
            return HttpResponse('not registered')
        
        model = get_model(app_label,model_name)
        
        fields = self.get_field_list(app_label = app_label, model_name = model_name)
        
        field_types = self.get_field_types(fields,model)
        
        if request.method!="POST":
            
            plugins = self.get_plugin_list(app_label, model_name)
            verbose = model._meta.verbose_name
            
            try:
                register = [[x[0],x[1],get_model(x[0],x[1])._meta.verbose_name.capitalize()] for x in self._meta.register]
            except AttributeError, e:
                raise ImproperlyConfigured("Please, check registered model names")

            context = {'app_label':app_label,
                       'model_name':model_name,
                       'register':register,
                       'sort':fields[0],
                       'plugins':plugins,
                       'verbose':verbose,
                       'field_types':field_types,
                       'prefix':self._meta.prefix,
                       'navigation':self._meta.navigation,
                       'GRID_ROWNUM':self._meta.grid_rownum,
                       'DIALOG_WIDTH':self._meta.dialog_width,
                       'DIALOG_MAX_HEIGHT':self._meta.dialog_max_height,
                       'WYSIWYG_HEIGHT':self._meta.wysiwyg_height,
                       'DATEPICKER_FORMAT':self._meta.datepicker_format,
                       'list_url': reverse('djgrid-listview', kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name}),
                       'inline_url':reverse('djgrid-inline', kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name}),
                       'create_url':reverse('djgrid-createview', kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name}),
                       }
            return render_to_response('djgrid/djgrid_listview.html',context, context_instance=RequestContext(request))
        
        if request.method=='POST':
                
            if 'initial' in request.POST:
                final = {}
                final['colModel'], final['colNames'] = Grid.make_column_structure(model, fields, app_label = app_label, model_name = model_name, safe = self.get_safe_list(model_name), inline = self._meta.inline, readonly = self._meta.readonly)
                return HttpResponse(simplejson.dumps(final),mimetype='application/json')
            
            else:
                queryset = model.objects.all()
                grid = Grid(queryset = queryset,
                            fields = fields,
                            post = request.POST,
                            app_label = app_label,
                            model_name = model_name,
                            model = model,
                            description = self._meta.description,
                            datetime_format = self._meta.datetime_format,
                            date_format = self._meta.date_format,
                            time_format = self._meta.time_format,
                            url_prefix = self._meta.prefix,
                            inline = self._meta.inline,
                            readonly = self._meta.readonly
                            )
                
                result  = grid.get_data()
                
                return HttpResponse(simplejson.dumps(result),mimetype='application/json')
                
    @check
    def inline(self, request,prefix, app_label, model_name, **kwargs):
        """
        inline model editing
        """
        if request.method=="POST" and self._meta.inline:
            fields = self.get_field_list(app_label = app_label,model_name = model_name)
            model = get_model(app_label, model_name)
            pk_field = model._meta.pk.name
            pk = request.POST.get(pk_field+'primarykey')
            instance = get_object_or_404(model, pk = pk)
            
            inline = []
            for field in fields:
                field_object = model._meta.get_field(field)
                field_type = field_object.__class__.__name__
                if field_type in Grid.INLINE_EDITABLE_FIELDS and not field_object.primary_key and field_object.editable:
                    inline.append(field)
            
            class InlineForm(forms.ModelForm):
                class Meta:
                    model = get_model(app_label,model_name)
                    fields = inline[:]
          
            aed = AED(request,
                      app_label,
                      model_name,
                      'djgrid/aed_base.html',
                      InlineForm,
                      pk,
                      force_ajax = True,
                      action = 'edit')
            aed.process_request() 
            result = {'status':'ok'}
            return HttpResponse(simplejson.dumps(result),mimetype='application/json')
        else:
            return HttpResponse('operation is not allowed')
    
    @check
    def actionview(self, request, prefix, app_label, model_name, object_id = None, action = None):
        """
        model instance add-edit-delete operations
        """
        
        class InstantForm(forms.ModelForm):
            formfield_callback = self.make_custom_field
            class Meta:
                model = get_model(app_label,model_name)
                
        url_add = reverse('djgrid-createview',kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name})
        if object_id:
            url_edit = reverse('djgrid-actionview',kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name,'object_id':object_id, 'action':'edit'})
            url_delete = reverse('djgrid-actionview',kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name,'object_id':object_id, 'action':'delete'})
        else:
            url_edit = None
            url_delete = None
                
        aed = AED(request,
                  app_label,
                  model_name,
                  'djgrid/aed_base.html',
                  InstantForm,
                  object_id,
                  extra_initial = {},
                  extra_context = {'WYSIWYG_HEIGHT':self._meta.wysiwyg_height},
                  force_ajax = False, 
                  action = action, 
                  url_add = url_add,
                  url_edit = url_edit, 
                  url_delete = url_delete)
        
        success_redirect_url = reverse('djgrid-listview',kwargs={'prefix':self._meta.prefix,'app_label': app_label,'model_name': model_name})
        aed.add_a_redirect(success_redirect_url)
        aed.add_e_redirect(success_redirect_url)
        aed.add_d_redirect(success_redirect_url)  
        
        return aed.process_request()


