from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from base.http import Http403
from jobs.models import Job
from jobs.forms import JobForm
from perms.models import ObjectPermission
from event_logs.models import EventLog

def index(request, id=None, template_name="jobs/view.html"):
    if not id: return HttpResponseRedirect(reverse('job.search'))
    job = get_object_or_404(Job, pk=id)
    
    if request.user.has_perm('jobs.view_job', job):
        log_defaults = {
            'event_id' : 255000,
            'event_data': '%s (%d) viewed by %s' % (job._meta.object_name, job.pk, request.user),
            'description': '%s viewed' % job._meta.object_name,
            'user': request.user,
            'request': request,
            'instance': job,
        }
        EventLog.objects.log(**log_defaults)
        return render_to_response(template_name, {'job': job}, 
            context_instance=RequestContext(request))
    else:
        raise Http403

def search(request, template_name="jobs/search.html"):
    query = request.GET.get('q', None)
    jobs = Job.objects.search(query)

    log_defaults = {
        'event_id' : 254000,
        'event_data': '%s searched by %s' % ('Job', request.user),
        'description': '%s searched' % 'Job',
        'user': request.user,
        'request': request,
        'source': 'jobs'
    }
    EventLog.objects.log(**log_defaults)
    
    return render_to_response(template_name, {'jobs':jobs}, 
        context_instance=RequestContext(request))

def print_view(request, id, template_name="jobs/print-view.html"):
    job = get_object_or_404(Job, pk=id)    

    log_defaults = {
        'event_id' : 255000,
        'event_data': '%s (%d) viewed by %s' % (job._meta.object_name, job.pk, request.user),
        'description': '%s viewed' % job._meta.object_name,
        'user': request.user,
        'request': request,
        'instance': job,
    }
    EventLog.objects.log(**log_defaults)
       
    if request.user.has_perm('jobs.view_job', job):
        return render_to_response(template_name, {'job': job}, 
            context_instance=RequestContext(request))
    else:
        raise Http403
    
@login_required
def edit(request, id, form_class=JobForm, template_name="jobs/edit.html"):
    job = get_object_or_404(Job, pk=id)

    if request.user.has_perm('jobs.change_job', job):    
        if request.method == "POST":
            form = form_class(request.user, request.POST, instance=job)
            if form.is_valid():
                job = form.save(commit=False)
                job.save()

                log_defaults = {
                    'event_id' : 252000,
                    'event_data': '%s (%d) edited by %s' % (job._meta.object_name, job.pk, request.user),
                    'description': '%s edited' % job._meta.object_name,
                    'user': request.user,
                    'request': request,
                    'instance': job,
                }
                EventLog.objects.log(**log_defaults)
                
                # remove all permissions on the object
                ObjectPermission.objects.remove_all(job)
                
                # assign new permissions
                user_perms = form.cleaned_data['user_perms']
                if user_perms:
                    ObjectPermission.objects.assign(user_perms, job)               
 
                # assign creator permissions
                ObjectPermission.objects.assign(job.creator, job) 
                                                              
                return HttpResponseRedirect(reverse('job', args=[job.pk]))             
        else:
            form = form_class(request.user, instance=job)

        return render_to_response(template_name, {'job': job, 'form':form}, 
            context_instance=RequestContext(request))
    else:
        raise Http403

@login_required
def add(request, form_class=JobForm, template_name="jobs/add.html"):
    if request.user.has_perm('jobs.add_job'):
        if request.method == "POST":
            form = form_class(request.user, request.POST)
            if form.is_valid():           
                job = form.save(commit=False)
                # set up the user information
                job.creator = request.user
                job.creator_username = request.user.username
                job.owner = request.user
                job.owner_username = request.user.username
                job.save()
 
                log_defaults = {
                    'event_id' : 251000,
                    'event_data': '%s (%d) added by %s' % (job._meta.object_name, job.pk, request.user),
                    'description': '%s added' % job._meta.object_name,
                    'user': request.user,
                    'request': request,
                    'instance': job,
                }
                EventLog.objects.log(**log_defaults)
                               
                # assign permissions for selected users
                user_perms = form.cleaned_data['user_perms']
                if user_perms:
                    ObjectPermission.objects.assign(user_perms, job)
                
                # assign creator permissions
                ObjectPermission.objects.assign(job.creator, job) 
                
                return HttpResponseRedirect(reverse('job', args=[job.pk]))
        else:
            form = form_class(request.user)
           
        return render_to_response(template_name, {'form':form}, 
            context_instance=RequestContext(request))
    else:
        raise Http403
    
@login_required
def delete(request, id, template_name="jobs/delete.html"):
    job = get_object_or_404(Job, pk=id)

    if request.user.has_perm('jobs.delete_job'):   
        if request.method == "POST":
            log_defaults = {
                'event_id' : 433000,
                'event_data': '%s (%d) deleted by %s' % (job._meta.object_name, job.pk, request.user),
                'description': '%s deleted' % job._meta.object_name,
                'user': request.user,
                'request': request,
                'instance': job,
            }
            
            EventLog.objects.log(**log_defaults)
            
            job.delete()
                
            return HttpResponseRedirect(reverse('job.search'))
    
        return render_to_response(template_name, {'job': job}, 
            context_instance=RequestContext(request))
    else:
        raise Http403