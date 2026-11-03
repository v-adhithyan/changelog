import json
import urllib.request
from collections import namedtuple
from datetime import datetime
from json import JSONDecodeError

import stringcase as stringcase
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from frontend.constants import INTEGRATION_EDITED_SUCCESSFULLY, \
    INTEGRATION_EDIT_FAILED_ERROR, INTEGRATION_NOT_AVAILABLE_FOR_PLAN_ERROR
from frontend.custom import views as custom_views
from frontend.custom.decorators import is_authenticated, is_admin
from frontend.custom.forms import TandoraForm
from frontend.views.integrations import slack
from v1.accounts.models import Subscription
from v1.integrations.webhooks.models import IncomingWebhook

integration_meta = namedtuple('integration_meta', 'name logo description')

INTEGRATION_FORM_FIELDS_DICT = {
    'zapier': {
        'read_only_fields': ['api_key'],
        'fields': ['api_key', 'zapier_trigger_scenario', 'active', ]
    },
    'webhooks': {
        'read_only_fields': [],
        'fields': ['name', 'url', 'trigger_when_created', 'trigger_when_published', 'active', ]
    },
    'twitter': {
        'read_only_fields': [],
        'fields': ['consumer_key', 'consumer_secret', 'access_token', 'access_token_secret', 'tweet_content',
                   'tweet_when_created', 'tweet_when_published',
                   'active', ]
    },
    'slack': {
        'read_only_fields': [],
        'fields': ['channel_to_post', 'trigger_when_created', 'trigger_when_published', 'active', ],
        'form': slack.SlackForm,
    },
    'incoming_webhook': {
        'read_only_fields': [],
        'exclude': ['company', 'hash', ]
    }
}

INTEGRATION_FRONTEND_META_DICT = {
    'zapier': {
        'logo': 'https://tandora-production.s3.amazonaws.com/assets/logos/zapier-logo.png',
        'description': 'Zapier provides workflows to automate the use of web applications together. '
                       'You can connect your favorite apps like Twitter, Facebook etc with Tandora '
                       'Changelog using Zapier Integration.'
                       'This enables you to seamlessly post Tandora Changelog to all of the connected Zapier Apps.'
                       'In a nutshell you can create a changelog once and post it to any of the connected Zapier Apps '
                       'using this integration.'
                       '<a style="color:blue;text-decoration:underline;" '
                       'href="/staff/manage/integrations/zapier/embed">Click here</a> '
                       'to view list of zaps available.'
    },
    'webhooks': {
        'logo': 'https://tandora-production.s3.amazonaws.com/assets/logos/webhooks-logo.png',
        'description': 'A Webhook helps to post data to your favorite app whenever a changelog is published '
                       'or created.'
                       'Zapier says they are a simple way your online accounts can "speak" to each other and get '
                       'notified automatically when something new happens.'
                       'In many cases, you\'ll need to know how to use webhooks if you want to '
                       'automatically push data from one app to another.'
    },
    'twitter': {
        'logo': 'https://tandora-production.s3.amazonaws.com/assets/logos/twitter-logo.png',
        'description': 'By activating Twitter integration you can tweet changelogs in the connected Twitter account.'
    },
    'slack': {
        'logo': 'https://tandora-production.s3.amazonaws.com/assets/logos/slack-logo.png',
        'description': 'Send all your changelogs to Slack in realtime.'
    },
    'incoming_webhook': {
        'logo': 'https://tandora-production.s3.amazonaws.com/assets/logos/webhooks-logo.png',
        'description': 'A incoming webhook will enable you to send data from external system to Tandora Changelog.'
                       'Whenever a incoming webhook is received in our end, a new changelog will be created.'
    }
}

INTEGRATION_EMBED_DICT = {
    'zapier': {
        'title': 'Tandora Changelog Zaps',
        'embed': '<script src="https://zapier.com/apps/embed/widget.js?services=tandora-changelog&limit=10"></script>'
    }
}

OAUTH_INTEGRATIONS = {
    'slack': {
        'oauth_start_helper': slack.oauth_start_helper,
    }
}


def uuid_form_value(self, value):
    # Patching UUIDField of forms here
    # This is because django form converts uuid field value to hex.
    # In zapier integration, we want users to copy api key from frontend
    # Without patching api key will appear as hex in frontend.
    # So patching the field so that original uuid value appears in frontend
    return value


class IntegrationList(custom_views.TandoraAdminListViewMixin):
    template_name = 'staff_v2/integrations/index.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = 'Manage Integrations'
        return context

    def get_queryset(self):
        return INTEGRATION_FRONTEND_META_DICT.keys()


@is_authenticated
@is_admin
def integration_form(request, integration):
    if not settings.DEBUG:
        try:
            subscription = request.user.company.subscription
            if not subscription.all_plan_features.get(integration):
                raise Subscription.DoesNotExist
        except Subscription.DoesNotExist:
            messages.warning(request, INTEGRATION_NOT_AVAILABLE_FOR_PLAN_ERROR)
            return HttpResponseRedirect(reverse('frontend-view-integrations'))
    model_class = apps.get_model('v1', stringcase.pascalcase(integration))
    instance, created = model_class.objects.get_or_create(company=request.user.company)
    integration_field_meta = INTEGRATION_FORM_FIELDS_DICT.get(integration, {})

    forms.UUIDField.prepare_value = uuid_form_value

    class IntegrationModelForm(forms.ModelForm):

        def __init__(self, *args, **kwargs):
            super(IntegrationModelForm, self).__init__(*args, **kwargs)

            for field in integration_field_meta.get('read_only_fields', []):
                self.fields[field].disabled = True

            if 'category' in self.fields:
                from v1.categories.models import Category
                self.fields['category'].required = True
                self.fields['category'].queryset = Category.objects.filter(company=request.user.company, deleted=False)

        class Meta:
            model = model_class
            if integration_field_meta.get('exclude'):
                exclude = integration_field_meta['exclude']
            elif integration_field_meta.get('fields'):
                fields = integration_field_meta['fields']
            else:
                fields = '__all__'

    if integration in OAUTH_INTEGRATIONS and not instance.oauth_done:
        helper = OAUTH_INTEGRATIONS[integration]['oauth_start_helper']
        html = helper(request)
        return render(request, 'staff_v2/postlogin_form.html', context={
            'extra': html
        })

    form_class = IntegrationModelForm if not integration_field_meta.get('form') else integration_field_meta['form']
    return TandoraForm(model_class, form_class, 'edit', 'staff_v2/postlogin_form.html',
                       reverse('frontend-view-integrations')) \
        .get_form(request,
                  success_message=INTEGRATION_EDITED_SUCCESSFULLY,
                  error_message=INTEGRATION_EDIT_FAILED_ERROR, instance=instance)


@is_authenticated
@is_admin
def embed_details(request, integration):
    try:
        context = INTEGRATION_EMBED_DICT[integration.lower()]
        return render(request, 'staff_v2/integration-embed.html', context=context)
    except KeyError:
        raise Http404


@require_POST
@csrf_exempt
def incoming_webhook_handler(request, hash_value):
    try:
        incoming_webhook = IncomingWebhook.objects.get(hash=hash_value)
        admin = incoming_webhook.company.admin_id
        request_data = json.loads(request.body)
        data = {
            'title': request_data.get(incoming_webhook.title_mapping),
            'content': request_data.get(incoming_webhook.content_mapping),
            'published': request_data.get(incoming_webhook.published_mapping) or incoming_webhook.published_value,
            'featured_image': request_data.get(incoming_webhook.featured_image_mapping),
            'category': incoming_webhook.category_id,
            'company': incoming_webhook.company_id,
            'created_by': admin,
            'last_edited_by': admin
        }
        from v1.core.serializers import ChangelogSerializer
        featured_image = data.pop('featured_image')
        serializer = ChangelogSerializer(data=data)
        if serializer.is_valid():
            changelog = serializer.save()

            try:
                if featured_image:
                    temp_img = NamedTemporaryFile(delete=True)
                    temp_img.write(urllib.request.urlopen(featured_image).read())
                    temp_img.flush()
                    changelog.featured_image.save(str(datetime.now().timestamp()), File(temp_img))
            except Exception as e:
                return JsonResponse({
                    'id': changelog.id,
                    'description': 'Changelog is created successfully but an expected error '
                                   'occurred while processing featured image.',
                    incoming_webhook.featured_image_mapping: e.__repr__(),
                })

            return JsonResponse({
                'id': changelog.id
            })

        errors = dict()
        if 'title' in serializer.errors:
            errors[incoming_webhook.title_mapping] = serializer.errors['title']
        if 'content' in serializer.errors:
            errors[incoming_webhook.content_mapping] = serializer.errors['content']

        return JsonResponse(errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except IncomingWebhook.DoesNotExist:
        raise Http404
    except JSONDecodeError:
        return JsonResponse({
            'error': 'Malformed JSON. Check post body.'
        }, status=status.HTTP_400_BAD_REQUEST)
