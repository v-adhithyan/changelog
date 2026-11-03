"""Populate the local development account with repeatable sample content."""
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from v1.accounts.models import Company
from v1.categories.models import Category
from v1.core.models import Changelog, PinnedChangelog
from v1.links.models import Link
from v1.settings.public_page.models import PublicPage


class Command(BaseCommand):
    help = 'Add sample changelogs and links to the local demo account.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo content can only be seeded in development.')
        company = Company.objects.get(admin__email='test@localhost.com')
        categories = {}
        for name, color in [('New', '#284BB0'), ('Announcement', '#8B5CF6'), ('Changes', '#0D9488')]:
            categories[name], _ = Category.objects.get_or_create(
                company=company, name=name, defaults={'color': color})
        posts = [
            ('welcome-to-tandora-demo', 'Welcome to the Tandora demo', 'Announcement', True,
             '<p>This demo workspace shows how a team can share product updates with its customers. Everything here is sample content.</p><h3>Explore the workspace</h3><ul><li>Browse published release notes on our public page.</li><li>Open the staff dashboard to edit posts and manage categories.</li><li>Visit our link hub for quick access to useful pages.</li></ul><p>Subscribe to the RSS feed to follow new announcements.</p>'),
            ('demo-rich-release-notes', 'Bring your release notes to life', 'New', True,
             '<p>Tell the full story behind every release with rich text, headings, images and links.</p><h3>What you can create</h3><ul><li>Feature announcements with clear examples.</li><li>Step-by-step guides for new workflows.</li><li>Short summaries of improvements and fixes.</li></ul><p>Use the editor in the dashboard to make your next update your own.</p>'),
            ('demo-categories', 'Find the updates that matter', 'Changes', True,
             '<p>Our sample updates are grouped into New, Changes and Announcement categories, making it easier to scan the latest news.</p><h3>A clearer release history</h3><p>Each update includes a category badge, publication date and a dedicated page that you can share with your customers.</p>'),
            ('demo-public-page', 'A public home for product updates', 'New', True,
             '<p>Customers can read published updates without creating an account or signing in.</p><ul><li>A clean overview of your recent releases.</li><li>Shareable pages for each announcement.</li><li>An RSS feed for readers who want to stay informed.</li></ul><p>Drafts remain inside the staff dashboard until you publish them.</p>'),
            ('demo-link-hub', 'All your useful links in one place', 'New', True,
             '<p>The company link hub brings your product updates, documentation and project resources together.</p><h3>Try it out</h3><p>Open the company public page to see a set of sample links. You can change their titles and destinations from Manage Links.</p>'),
            ('demo-small-improvements', 'Small improvements, smoother days', 'Changes', True,
             '<p>This sample maintenance update demonstrates a short, practical release note.</p><ul><li>Clearer labels throughout the workspace.</li><li>More readable category badges.</li><li>A simpler path from an announcement to its full details.</li></ul><p>Thanks for exploring the demo!</p>'),
            ('demo-draft-next-release', 'Draft: next release announcement', 'Announcement', False,
             '<p>This is a sample draft. Replace this introduction with the story behind your next release.</p><h3>Before publishing</h3><ul><li>Add the final feature details.</li><li>Include helpful screenshots or links.</li><li>Check the category and preview the content.</li></ul>'),
            ('demo-draft-feedback', 'Draft: share your feedback', 'Changes', False,
             '<p>Use this sample draft as a starting point for a customer feedback announcement. Add your real feedback destination before publishing.</p>'),
        ]
        for index, (slug, title, category, published, content) in enumerate(posts):
            post, created = Changelog.objects.get_or_create(
                company=company, slug=slug,
                defaults=dict(title=title, content=content, category=categories[category],
                              published=published, created_by=company.admin,
                              last_edited_by=company.admin))
            if created:
                Changelog.objects.filter(pk=post.pk).update(
                    created_at=timezone.now() - timedelta(days=index * 3),
                    last_edited_at=timezone.now() - timedelta(days=index * 3))
        covers = {
            'welcome-to-tandora-demo': 'welcome',
            'demo-rich-release-notes': 'editor',
            'demo-categories': 'categories',
            'demo-public-page': 'public',
            'demo-link-hub': 'links',
            'demo-small-improvements': 'improvements',
        }
        for slug, cover in covers.items():
            artwork = Path(settings.BASE_DIR) / 'frontend/static/public/covers' / (cover + '.png')
            post = Changelog.objects.get(company=company, slug=slug)
            if artwork.exists() and not post.featured_image:
                with artwork.open('rb') as image:
                    post.featured_image.save('demo-covers/' + cover + '.png', File(image))
        featured = Changelog.objects.get(company=company, slug='welcome-to-tandora-demo')
        PinnedChangelog.objects.get_or_create(company=company, defaults={'changelog': featured})
        public, _ = PublicPage.objects.get_or_create(company=company)
        if not public.banner_title:
            public.banner_title = 'Tandora product updates'
            public.banner_tag_line = 'Release notes, improvements and announcements from our demo workspace.'
            public.seo_title = 'Tandora demo | Product updates'
            public.save()
        root = settings.HOST.rstrip('/')
        Site.objects.get_or_create(domain=urlparse(root).hostname, defaults={'name': 'Tandora local demo'})
        links = [
            ('Read our product updates', root + '/tandoradev/test'),
            ('About this demo', root + '/tandoradev/test/welcome-to-tandora-demo'),
            ('Browse the project on GitHub', 'https://github.com/tandoraco/changelog'),
            ('Subscribe to release notes (RSS)', root + '/tandoradev/test/rss'),
        ]
        for title, url in links:
            Link.objects.get_or_create(company=company, title=title, defaults={'url': url})
        self.stdout.write(self.style.SUCCESS(
            'Demo ready: 6 published updates, 2 sample drafts, 4 links and a pinned welcome post.'))
