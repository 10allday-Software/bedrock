# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render as django_render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from django.views.generic import TemplateView

from lib import l10n_utils
from lib.l10n_utils import L10nTemplateView, get_locale
from lib.l10n_utils.fluent import ftl_file_is_active

from bedrock.contentful.api import contentful_home_page
from bedrock.contentful.models import ContentfulEntry
from bedrock.mozorg.credits import CreditsFile
from bedrock.mozorg.forums import ForumsFile
from bedrock.pocketfeed.models import PocketArticle

from commonware.decorators import xframe_allow

credits_file = CreditsFile('credits')
forums_file = ForumsFile('forums')

TECH_BLOG_SLUGS = ['hacks', 'cd', 'futurereleases']


def csrf_failure(request, reason=''):
    template_vars = {'reason': reason}
    return l10n_utils.render(request, 'mozorg/csrf-failure.html', template_vars,
                             status=403)


@xframe_allow
def hacks_newsletter(request):
    return l10n_utils.render(request,
                             'mozorg/newsletter/hacks.mozilla.org.html')


@require_safe
def credits_view(request):
    """Display the names of our contributors."""
    ctx = {'credits': credits_file}
    # not translated
    return django_render(request, 'mozorg/credits.html', ctx)


@require_safe
def forums_view(request):
    """Display our mailing lists and newsgroups."""
    ctx = {'forums': forums_file}
    return l10n_utils.render(request, 'mozorg/about/forums/forums.html', ctx)


class Robots(TemplateView):
    template_name = 'mozorg/robots.txt'
    content_type = 'text/plain'

    def get_context_data(self, **kwargs):
        hostname = self.request.get_host()
        return {'disallow_all': not hostname == 'www.mozilla.org'}


NAMESPACES = {
    'addons-bl': {
        'namespace': 'http://www.mozilla.org/2006/addons-blocklist',
        'standard': 'Add-ons Blocklist',
        'docs': 'https://wiki.mozilla.org/Extension_Blocklisting:Code_Design',
    },
    'em-rdf': {
        'namespace': 'http://www.mozilla.org/2004/em-rdf',
        'standard': 'Extension Manifest',
        'docs': 'https://developer.mozilla.org/en/Install_Manifests',
    },
    'microsummaries': {
        'namespace': 'http://www.mozilla.org/microsummaries/0.1',
        'standard': 'Microsummaries',
        'docs': 'https://developer.mozilla.org/en/Microsummary_XML_grammar_reference',
    },
    'mozsearch': {
        'namespace': 'http://www.mozilla.org/2006/browser/search/',
        'standard': 'MozSearch plugin format',
        'docs': 'https://developer.mozilla.org/en/Creating_MozSearch_plugins',
    },
    'update': {
        'namespace': 'http://www.mozilla.org/2005/app-update',
        'standard': 'Software Update Service',
        'docs': 'https://wiki.mozilla.org/Software_Update:Testing',
    },
    'xbl': {
        'namespace': 'http://www.mozilla.org/xbl',
        'standard': 'XML Binding Language (XBL)',
        'docs': 'https://developer.mozilla.org/en/XBL',
    },
    'xforms-type': {
        'namespace': 'http://www.mozilla.org/projects/xforms/2005/type',
        'standard': 'XForms mozType extension',
        'docs': 'https://developer.mozilla.org/en/XForms/Custom_Controls',
    },
    'xul': {
        'namespace': 'http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul',
        'standard': 'XML User Interface Language (XUL)',
        'docs': 'https://developer.mozilla.org/en/XUL',
    },
}


def namespaces(request, namespace):
    context = NAMESPACES[namespace]
    context['slug'] = namespace
    template = 'mozorg/namespaces.html'
    return django_render(request, template, context)


class ContributeView(L10nTemplateView):
    ftl_files_map = {
        'mozorg/contribute/contribute-2020.html': ['mozorg/contribute']
    }

    def get_template_names(self):
        if ftl_file_is_active('mozorg/contribute'):
            template_name = 'mozorg/contribute/contribute-2020.html'
        else:
            template_name = 'mozorg/contribute/index.html'

        return [template_name]


class HomePageView(L10nTemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_data = ContentfulEntry.objects.get_homepage()
        ctx['card_layouts'] = page_data['layouts'] if page_data else []
        ctx['pocket_articles'] = PocketArticle.objects.all()[:4]
        return ctx

    def get_template_names(self):
        return [
            'mozorg/contentful-preview.html'
        ]


@method_decorator(never_cache, name='dispatch')
class HomePagePreviewView(L10nTemplateView):
    locales_map = {
        'en': 'en-US',
    }

    def get_template_names(self):
        return [
            'mozorg/contentful-preview.html'
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_data = contentful_home_page.get_page_data(ctx['content_id'])
        entry_data = contentful_home_page.get_entry_data(ctx['content_id'])
        info =contentful_home_page.get_info_data(ctx['content_id'])
        body = contentful_home_page.get_body(ctx['content_id'])
        hero_data = contentful_home_page.get_hero_data(ctx['content_id'])
        callout_data = contentful_home_page.get_callout_data(ctx['content_id'])
        ctx['card_layouts'] = page_data['layouts']
        ctx['page_data'] = page_data if page_data else ['']
        ctx['entry_data'] = entry_data if entry_data else ['']
        ctx['info'] = info if info else ['']
        ctx['body'] = body if body else ['']
        ctx['hero_data'] = hero_data if hero_data else ['']
        ctx['callout_data'] = callout_data if callout_data else ['']
        return ctx

    def render_to_response(self, context, **response_kwargs):
        return super().render_to_response(context, **response_kwargs)
