from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import get_user_model

from amon.apps.users.forms import InviteForm, InviteNewUserForm
from amon.apps.users.models import invite_model
from amon.apps.notifications.mail.models import email_model
from amon.apps.users.emails import send_invitation_email, send_revoked_email

User = get_user_model()


@user_passes_test(lambda u: u.is_superuser)
@login_required
def view_users(request):

    email_settings = email_model.get_email_settings()

    if request.method == 'POST':
        form = InviteForm(request.POST, user=request.user)
        if form.is_valid():
            new_invite = form.save()

            try:
                send_invitation_email(new_invite)
                messages.add_message(request, messages.INFO, 'Invitation sent.')
            except Exception as e:
                messages.add_message(request, messages.ERROR, "Error sending email invite. Please check your SMTP settings.")

            return redirect(reverse('view_users'))
    else:
        form = InviteForm()


    active_users = User.objects.filter(is_superuser=False)
    pending = invite_model.get_all()
    
    
    return render_to_response('users/view.html', {
        "form": form,
        "active_users": active_users,
        "pending": pending,
        "email_settings": email_settings,
    },
    context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
@login_required
def revoke_access(request, user_id=None):

    user = User.objects.get(id=user_id)
    
    send_revoked_email(user=user)
    user.delete()
            
        
    messages.add_message(request, messages.INFO, 'Access revoked.')
    return redirect(reverse('view_users'))


@user_passes_test(lambda u: u.is_superuser)
@login_required
def remove_pending(request, invitation_id=None):

    invite_model.delete(invitation_id)    
        
    messages.add_message(request, messages.INFO, 'Invitation removed.')
    return redirect(reverse('view_users'))


def confirm_invite(request, invitation_code=None):

    invite = invite_model.collection.find_one({'invitation_code': invitation_code})
    if invite is None:
        raise Http404
    
    if request.method == 'POST':
        form = InviteNewUserForm(request.POST, invite=invite)
        if form.is_valid():
            form.save()


            return redirect(reverse('login'))
    else:
        form = InviteNewUserForm(invite=invite)

    return render_to_response('users/confirm_invite.html', {
        "form": form,
        "invite": invite,
        "domain_url": settings.HOST

    },
    context_instance=RequestContext(request))