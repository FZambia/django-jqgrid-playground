import time as tm
import math, operator, traceback
from datetime import datetime,date,time
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.db.models import get_model, Sum, Q
from django.utils.encoding import smart_unicode
from django.core.exceptions import ImproperlyConfigured

# Create your models here.
class Grid(object):
    """
    jqgrid-python helper class
    """
    UNDEFINED = 'undefined'
    
    INTEGER_FIELDS = ['IntegerField',
                      'SmallIntegerField',
                      'PositiveIntegerField',
                      'PositiveSmallIntegerField',
                      'BigIntegerField',
                      'BooleanField']
    
    FLOAT_FIELDS = ['FloatField',
                    'DecimalField']
    
    TOTAL_FIELDS = INTEGER_FIELDS+FLOAT_FIELDS
    
    DATE_FIELDS = ['DateTimeField',
                   'DateField',
                   'TimeField']

    INLINE_EDITABLE_FIELDS = ['IntegerField',
                              'SmallIntegerField',
                              'PositiveSmallIntegerField',
                              'CharField',
                              'TextField',
                              'DateTimeField',
                              'DateField',
                              'TimeField',
                              'GenericIPAddressField',
                              'BigIntegerField',
                              'BooleanField',
                              'EmailField',
                              'IPAddressField',
                              'SlugField',
                              'TextField',
                              'URLField',
                              'XMLField']
 
    def __init__(self,
                 queryset = [],
                 fields=[],
                 post = {},
                 app_label=None,
                 model_name=None, 
                 model = None,
                 inline = True,
                 readonly = False,
                 description = {},
                 datetime_format = "%d.%m.%Y %H:%M:%s",
                 date_format = "%d.%m.%Y",
                 time_format = "%H:%M",
                 url_prefix = 'jqgrid-admin',
                 **kwargs):
        
        self.queryset = queryset
        
        self.fields = fields
        self.exclude = []
        
        self.post = post
        self.search = ('_search' in self.post and self.post['_search']=='true')
        
        try:
            self.page = int(self.post['_page'])
            self.limit = int(self.post['_rows'])
            self.sidx = self.post['_sidx']
            self.sord = self.post['_sord']
        except:
            raise ImproperlyConfigured("For grid render 'post' parameter should contain correct information about page, limit, sidx and sord") 
        
        self.count = None
        self.total_pages = None
        self.start = None      
                        
        self.result = {}
        self.result['userdata'] = {}        
        self.result['userdata'][self.fields[0]] = 'Totals'
        
        self.app_label = app_label
        self.model_name = model_name
                
        if model:
            self.model = model
        else:
            self.model = get_model(app_label,model_name)
    
        self.inline = inline
        self.readonly = readonly
                
        self.description = description
        
        self.url_prefix = url_prefix
        
        self.datetime_format = datetime_format
        self.date_format = date_format
        self.time_format = time_format
        
    @classmethod    
    def make_column_structure(cls, model, fields, safe = [], inline = True, readonly = False, app_label = None, model_name = None, **kwargs):
        """
        constructs jqgrid colmodel and colnames to render the grid
        """
        colnames = []
        colmodel = []
        
        if inline:
            pk_field = model._meta.pk.name
            colmodel.append({'name':pk_field+'primarykey',
                             'index':pk_field+'primarykey',
                             'hidden':True,
                             'editable':True})
            colnames.append(pk_field+'primarykey')
    
        for field in fields:
            field_object = model._meta.get_field(field)
            field_type = field_object.__class__.__name__
            hash = {}
            hash['name'] = field
            hash['index'] = field
            hash['width'] = 100
            hash['align'] = 'center'
            if field_type in Grid.INLINE_EDITABLE_FIELDS and not field_object.primary_key and inline and field_object.editable:
                hash['editable'] = True
            if field_type in Grid.FLOAT_FIELDS:
                hash['formatter'] = 'number'
            if field in safe:
                hash['formatter'] = 'safe_formatter'
            
            colmodel.append(hash)
            colnames.append(field_object.verbose_name.lower())
            
        if not readonly:
            colmodel.append({'name':'actions',
                             'index':'actions',
                             'width':100,
                             'formatter':'safe_formatter',
                             'align':'center',
                             'sortable':False})
            colnames.append('actions')      
        
        return (colmodel,colnames)       
    
    def construct_search(self, field, value, field_type = 'CharField'):
        if field_type in Grid.INTEGER_FIELDS:
            modifier = int
        elif field_type in Grid.FLOAT_FIELDS:
            modifier = float
        else:
            modifier = smart_unicode
        if value.startswith('^'):
            return ("%s__istartswith" % field, modifier(value[1:]))
        elif value.startswith('='):
            return ("%s__iexact" % field, modifier(value[1:]))
        elif value.startswith('$'):
            return ("%s__iendswith" % field, modifier(value[1:]))
        elif value.startswith('>'):
            return ("%s__gt" % field, modifier(value[1:]))
        elif value.startswith('<'):
            return ("%s__lt" % field, modifier(value[1:]))
        else:
            return ("%s__icontains" % field, modifier(value))
 
 
    def common_filter(self):
        """
        filter queryset
        """
        filter_hash = {}
        for param in self.post:
            if param in self.fields and param not in self.exclude:
                field_object = self.model._meta.get_field(param)
                field_type = field_object.__class__.__name__
                k,v = self.construct_search(param, self.post[param], field_type = field_type)
                filter_hash[k]=v
        print filter_hash
        try:
            self.queryset = self.queryset.filter(**filter_hash)
        except:
            traceback.print_exc()
        
        return True
    
    
    def date_filter(self, field, value):
        """
        filter queryset by date
        """
        try:
            start = datetime.strptime(value, self.date_format)
        except:
            start = datetime(*(tm.strptime(value, self.date_format)[0:6])) 
        try:      
            finish = datetime.strptime(value+' 23:59:59',self.date_format+" %H:%M:%S")
        except:
            finish = datetime(*(tm.strptime(value+' 23:59:59', self.date_format+" %H:%M:%S")[0:6]))
        
        filter_hash = {field+'__gte':start,field+'__lte':finish}
        
        self.queryset = self.queryset.filter(**filter_hash)
        
        return True

    def related_filter(self, field, value):
        try:
            self.description[self.model_name]['search'][field]
        except:
            traceback.print_exc()
        else:
            orm_lookups = dict(self.construct_search('%s__%s' % (field,f),value) for f in self.description[self.model_name]['search'][field])
            or_queries = [Q(**{k:v}) for k,v in orm_lookups.iteritems()]
            self.queryset = self.queryset.filter(reduce(operator.or_, or_queries))

        return True
            
    def get_total_pages(self):
        """
        total amount of pages for this model
        """
        if self.count>0:
            return int(math.ceil(self.count/self.limit))+1
        else:
            return 1
    

    def get_edit_url(self, instance_id, app_label, model_name):
        return reverse('djgrid-actionview',kwargs={'prefix':self.url_prefix, 'app_label': app_label,'model_name': model_name,'object_id':instance_id, 'action':'edit'})

    
    def get_delete_url(self, instance_id, app_label, model_name):
        return reverse('djgrid-actionview',kwargs={'prefix':self.url_prefix, 'app_label': app_label,'model_name': model_name,'object_id':instance_id,'action':'delete'})
    
    
    def get_action_urls(self,instance_id):
        """
        returns action button's html for certain row
        """
        edit_url = self.get_edit_url(instance_id, self.app_label, self.model_name)
        delete_url = self.get_delete_url(instance_id, self.app_label, self.model_name)
        return mark_safe('<a href="%s" class="modal edit">Edit</a>&nbsp&nbsp<a href="%s" class="modal delete">Delete</a>' % (edit_url, delete_url,))
    
    def analize(self, value, field_type, id):
        if field_type=='DateTimeField':
            try:
                value = datetime.strftime(value,self.datetime_format)
            except:
                value = Grid.UNDEFINED
        elif field_type=='DateField':
            try:
                value = datetime.strftime(value, self.date_format)
            except:
                value = Grid.UNDEFINED
        elif field_type=='TimeField':
            try:
                value = datetime.strftime(value, self.time_format)
            except:
                value = Grid.UNDEFINED
        elif field_type=='BooleanField':
            if value==True:
                value = 1
            else:
                value = 0
        elif field_type in ['ForeignKey','OneToOneField']:
            try:
                value = '<a href="%s" title="%s">%s</a>' % (value.get_absolute_url(), smart_unicode(value) )
            except:
                value = smart_unicode(value)
        elif field_type in ['FileField','ImageField']:
            try:
                value = value.name
            except:
                value = Grid.UNDEFINED          
        return value

    def filter(self):
        if not self.search:
            return
        for field in self.fields:
            if field in self.post:
                field_object = self.model._meta.get_field(field)
                field_type = field_object.__class__.__name__
                value = self.post[field]
                
                if field_type in ['ForeignKey','OneToOneField']:
                    self.exclude.append(field)
                    self.related_filter(field, value)
                    
                elif field_type in Grid.DATE_FIELDS:
                    self.exclude.append(field)
                    self.date_filter(field, value)
                    
        self.common_filter()

    def order(self):
        if self.sidx:
            if self.sord=='asc':    
                self.queryset = self.queryset.order_by('-'+self.sidx)
            else:
                self.queryset = self.queryset.order_by(self.sidx)
    
    def aggregate(self):
        for field in self.fields:
            try:
                if self.model._meta.get_field(field).__class__.__name__ in Grid.TOTAL_FIELDS:
                    self.result['userdata'][field] = float(self.queryset.aggregate(Sum(field))[field+'__sum'])        
            except:
                pass
    
    def paginate(self):
        self.count = self.queryset.count()
        self.total_pages = self.get_total_pages()
        if self.page>self.total_pages:
            self.page = self.total_pages
        self.start = self.limit*self.page-self.limit
        
        self.queryset = self.queryset[self.start:self.start+self.limit]    
        self.result['page']=self.page
        self.result['total']=self.total_pages
        self.result['records']=self.count
    
    def get_data(self):
        # filtering
        self.filter()
        # ordering by sidx
        self.order()
        # aggregate total sum
        self.aggregate()
        # pagination operations   
        self.paginate()
        
        self.result['rows']=[]
        
        pk_field = self.queryset.model._meta.pk.name
        
        for item in self.queryset:
            row = {}
            row['cell'] = []
            
            if self.inline:
                row['cell'].append(getattr(item,pk_field))
         
            for index,field in enumerate(self.fields):
                field_type = item._meta.get_field(field).__class__.__name__
                pk = getattr(item,pk_field)
                try:
                    val = getattr(item,field)
                except:
                    val = None
                value = self.analize(val, field_type, pk) 
                row['cell'].append(value)
            
            if not self.readonly:
                row['cell'].append(self.get_action_urls(pk))
                 
            self.result['rows'].append(row)
            
        return self.result