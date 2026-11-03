from django.contrib import messages
from django.urls import reverse

from frontend.constants import LINK_CREATED_SUCCESSFULLY, LINK_DOES_NOT_EXIST, LINK_DELETED_SUCCESSFULLY
from frontend.custom.decorators import is_authenticated
from frontend.custom.forms import TandoraForm
from frontend.custom.utils import delete_model
from frontend.custom.views import TandoraListViewMixin
from frontend.forms.links import LinkForm
from v1.links.models import Link


class LinksList(TandoraListViewMixin):
    template_name = 'staff_v2/links/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Manage Links'


        return context

    def get_queryset(self):
        company_id = self.request.session['company-id']
        return Link.objects.filter(company__id=company_id)


@is_authenticated
def link_form(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['company'] = request.user.company.id
    else:
        post_data = None

    return TandoraForm(Link, LinkForm, 'create', 'staff_v2/postlogin_form.html',
                       '/staff/manage/links') \
        .get_form(request, success_message=LINK_CREATED_SUCCESSFULLY,
                  post_data=post_data)


@is_authenticated
def edit_link(request, id):
    return TandoraForm(Link, LinkForm, 'edit', 'staff_v2/postlogin_form.html',
                       '/staff/manage/links') \
        .get_form(request,
                  success_message=LINK_CREATED_SUCCESSFULLY,
                  error_message=LINK_DOES_NOT_EXIST,
                  id=id)


@is_authenticated
def delete_link(request, id):
    return delete_model(request, Link, id, reverse('frontend-view-links'), '/staff/manage/links',
                        LINK_DELETED_SUCCESSFULLY,
                        LINK_DOES_NOT_EXIST)
