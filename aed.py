# -*- coding: utf-8 -*-
"""
Class for adding,editing,deleting model instance
Created by FZambia
MIT License
VERSION 0.2

Parameters:
    - request - just a django standart request
    - app_name:string - application name, e.g. 'activity'
    - model_name:string - case insensetive model name, e.g 'post'
    - template_name:string - template name to render
    - form_class:django.forms.models.ModelFormMetaclass - model form , e.g PostForm
    - id:integer or None - primary key of object, if id is None then this function will create new object, else will edit existing with this id
    - extra_initial:dict - dict of params that must be added to form as initial values for fields. e.g. {'activity':activity.id}
    - extra_context:dict - dict of params that must be added to template context. e.g. {'model':'post'}
    - force_ajax:boolean - force class to act ajax-way
    - action:string or None - used only to define deletion
    - url_edit:string or None - redirect after editing
    - url_add:string or None - redirect after adding
    - url_delete:string or None - redirect after deleting

Methods:
    - add_(a/e/d)_callback(function) - add a callback to do something with object after adding,editing or before deleting
    - add_(a/e/d)_redirect(url) - add a redirect url to go after adding,editing or deleting
    - set_unused_fields(list) - list of fields that need to be excluded from the form
    - set_unused_fields(list) - list of fields that need to be excluded from the form
    - set_result_success - sets json response of succesful operation in ajax mode
    - set_result_fail - sets json response of unsuccesful operation in ajax mode
 
Requirements:
    - object must have get_absolute_url() method
    - can not pass to extra_context params with keys: 'form','id','object'
    - you should use native form templates of this app. Of course you can easily modify it's design, but do not touch logic

Using:
    for example, you want to create add-edit-delete for model "Post" of app "Blog"
    First, you need to specify urls for this operations.
    
    from django.conf.urls.defaults import *
    import views
    urlpatterns = patterns('blog.views',
        url(r'^/$', views.blog_index, name="blog_index"),
        url(r'/(?P<id>\d+)/$', views.post_detail, name="post_detail"),
        url(r'/add/$',views.post_add_edit_delete, name="post_add"),
        url(r'(?P<id>\d+)/(?P<action>\w+)/$',views.post_add_edit_delete, name="post_action"),
    )
    
    It's up to you to manage first two urls, that display all posts and post detail.
    The most interesting are 3-rd and 4-th urls. Both of them link to one view.
    Now let's have a look at post_add_edit_delete view function:
    
    from aed.models import Aed # importing class for add-edit-delete
    from django.core.urlresolvers import reverse
    
    def post_add_edit_delete(request, id = None, action = None):
        # define urls that will be used in form template
        url_add = reverse('post_add',kwargs = {})
        if id:
            url_edit = reverse('post_action',kwargs = {'id':id,'action':'edit'})
            url_delete = reverse('post_action',kwargs = {'id':id,'action':'delete'})
        else:
            url_edit = url_delete = None
        aed = AED(request,'blog','post','forms/general_form_ajax.html',PostForm,id,extra_initial = {},extra_context = {}, force_ajax = False, action = action, url_add = url_add, url_edit = url_edit, url_delete = url_delete)
        aed.add_d_redirect('/events/') # custom url to redirect after deleting object
        aed.add_e_callback(notify) # custom callback after editing object
        return aed.process_request() # do class main work

    Now it's almost over. All you need to do is to write notify function that you define as edit callback. It can be something like this:
    
    def notify(*args,**kwargs):
        obj = kwargs['obj']
        request = kwargs['request']
        header = obj.header
        updated_by = request.user
        # DO SOMETHING , for example send mail, log etc.
        
"""

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response,get_object_or_404
from django.utils import simplejson
from django.db.models import get_model
from django.template import RequestContext
from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages

class AED(object):
    def __init__(self,request,app_name,model_name,template_name,form_class,id=None,extra_initial = {},extra_context = {},force_ajax=False, action = None, url_add = None, url_edit = None, url_delete = None):
        self.request = request
        self.app_name = app_name
        self.model_name = model_name
        self.template_name = template_name
        self.form_class = form_class
        self.id = id
        self.extra_initial = extra_initial
        self.extra_context = extra_context
        self.action = action
        self.url_add = url_add
        self.url_edit = url_edit
        self.url_delete = url_delete
        self.is_ajax = self.check_ajax(force_ajax)
        self.model = get_model(self.app_name,self.model_name)
        self.obj = self.get_object()
        self.form = None
        self.e_callbacks = []
        self.a_callbacks = []
        self.d_callbacks = []
        self.e_redirect = None
        self.a_redirect = None
        self.d_redirect = None
        self.result_success = {'result':'OK','msg':"reload"}
        self.result_fail = {'result':'Fail'}
        self.unused_fields = []
        self.a_messages = []
        self.e_messages = []
        self.d_messages = []

    def add_a_callback(self,function):
        """
        adds callback after adding object
        """
        self.a_callbacks.append(function)
        
    def add_e_callback(self,function):
        """
        adds callback after editing object
        """
        self.e_callbacks.append(function)
        
    def add_d_callback(self,function):
        """
        adds callback before deleting object
        """
        self.d_callbacks.append(function)

    def add_a_redirect(self,url):
        """
        adds redirect url after adding instance
        """
        self.a_redirect = url

    def add_e_redirect(self,url):
        """
        adds redirect url after editing instance
        """
        self.e_redirect = url
        
    def add_d_redirect(self,url):
        """
        adds redirect url after deleting instance
        """
        self.d_redirect = url
        
    def add_a_messages(self,*msgs):
        """
        adds django.contrib message after adding instance
        """
        for msg in msgs:
            self.a_messages.append(msg)
        
    def add_e_messages(self,*msgs):
        """
        adds django.contrib message after editing instance
        """
        for msg in msgs:
            self.e_messages.append(msg)
        
    def add_d_messages(self,*msgs):
        """
        adds django.contrib message after deleting instance
        """
        for msg in msgs:
            self.d_messages.append(msg)
    
    def set_result_success(self,result):
        """
        @param result:dict
        sets response of succesful operation in ajax mode
        """
        self.result_success = result
        
    def set_result_fail(self,result):
        """
        @param result:dict
        sets response of unsuccesful operation in ajax mode
        """
        self.result_fail = result
    
    def set_unused_fields(self,fields):
        """
        @param fields:list
        sets fields that will be deleted from form
        """
        self.unused_fields = fields    
        
    def check_ajax(self,force_ajax):
        """
        defines ajax or non-ajax mode
        """
        return self.request.is_ajax() or force_ajax
    
    def get_object(self):
        """
        returns instance by id or new instance of model
        """
        if self.id:
            obj = get_object_or_404(self.model,pk=self.id)
        else:
            obj = self.model()
        return obj
    
    def process_callbacks(self,callbacks):
        """
        @param callbacks : list of callables
        executes callbacks
        """
        for callback in callbacks:
            callback(obj = self.obj, form = self.form, request = self.request)
    
    def process_messages(self,msgs):
        """
        @param messages : list of messages
        add messages to response
        """
        for msg in msgs:
            messages.add_message(self.request, messages.INFO, msg)
    
    def delete_object(self):
        """
        deletes object
        """
        self.process_callbacks(self.d_callbacks)
        self.obj.delete()
        self.process_messages(self.d_messages)
        if self.d_redirect:
            return HttpResponseRedirect(self.d_redirect)
        if not self.is_ajax:
            return HttpResponseRedirect('../../')
        else:
            return HttpResponse(simplejson.dumps(self.result_success),mimetype='application/json')        
    
    def remove_unused_fields(self):
        """
        removes unused fields from the form instance
        """
        for field in self.unused_fields:
            if self.form.fields[field].required:
                raise ImproperlyConfigured("One of unused fields you specified is required for the form")
            try:
                del self.form.fields[field]
            except:
                raise ImproperlyConfigured("One of unused fields you specified does not exist in the form")
    
    def get_context(self):
        """
        fills context with data
        """
        context = {'form':self.form,'id':self.id,'object':self.obj,'is_ajax':self.is_ajax}
        if self.id is not None:
            if self.url_edit:
                context['url'] = self.url_edit
            if self.url_delete:
                context['url_delete'] = self.url_delete
        else:
            if self.url_add:
                context['url'] = self.url_add
        if self.extra_context:        
            for key,value in self.extra_context.iteritems():
                context[key] = value
        return context
    
    def process_request(self):
        """
        decides what to do with request
        """
        if self.id and self.action and self.action=='delete':
            return self.delete_object()
        if self.request.method=="POST":
            return self.process_post()
        else:
            return self.process_get()
    
    def process_post(self):
        """
        does POST work when form was submited
        """
        self.form = self.form_class(instance = self.obj, data = self.request.POST, files = self.request.FILES)
        self.remove_unused_fields()
        if self.form.is_valid():
            self.obj = self.form.save()
            if self.id is not None:
                self.process_callbacks(self.e_callbacks)
                self.process_messages(self.e_messages)
            else:
                self.process_callbacks(self.a_callbacks)
                self.process_messages(self.a_messages)
            if not self.is_ajax:
                if not self.id:
                    if self.a_redirect:
                        return HttpResponseRedirect(self.a_redirect)
                else:
                    if self.e_redirect:
                        return HttpResponseRedirect(self.e_redirect)
                return HttpResponseRedirect(self.obj.get_absolute_url())
            else:
                return HttpResponse(simplejson.dumps(self.result_success),mimetype='application/json')
        else:
            if not self.is_ajax:
                context = self.get_context()
                return render_to_response(self.template_name, context, context_instance=RequestContext(self.request))
            else:
                self.result_fail['msg'] = self.form.errors
                return HttpResponse(simplejson.dumps(self.result_fail),mimetype='application/json')     
    
    def process_get(self):
        """
        just displays instance form
        """
        initial = {}
        for key,value in self.extra_initial.iteritems():
            initial[key] = value
        self.form = self.form_class(instance = self.obj,initial=initial)
        self.remove_unused_fields()
        context = self.get_context()
        return render_to_response(self.template_name, context, context_instance=RequestContext(self.request))